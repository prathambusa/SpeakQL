import io
import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.config import settings
from backend.db.connection import get_engine, register_engine, remove_engine
from backend.db.introspect import introspect_schema
from backend.db.registry import all_aliases as dynamic_db_aliases
from backend.db.registry import deregister as registry_deregister
from backend.db.registry import get_kpis, set_kpis, remove_kpis
from backend.db.registry import get_suggestions, set_suggestions, remove_suggestions
from backend.db.registry import load as load_registry
from backend.db.registry import register as registry_register
from backend.models import (
    ConnectRequest,
    ConnectResponse,
    DatabaseInfo,
    DatabaseListResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    RefreshResponse,
    SchemaResponse,
)
from backend.pipeline.agent import generate_sql
from backend.pipeline.kpis import compute_kpis
from backend.pipeline.suggestions import generate_suggestions
from backend.pipeline.executor import (
    QueryExecutionError,
    QueryTimeoutError,
    execute_query,
)
from backend.pipeline.formatter import SQLValidationError, detect_dialect, format_sql
from backend.pipeline.retriever import (
    delete_index,
    index_tables,
    is_collection_empty,
    retrieve_tables,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

UPLOADS_DIR = Path("/app/uploads")


async def _get_table_names(engine) -> list[str]:
    from sqlalchemy import inspect

    def _sync(conn):
        return inspect(conn).get_table_names()

    async with engine.connect() as conn:
        return await conn.run_sync(_sync)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_registry()
    for alias, url in dynamic_db_aliases().items():
        try:
            register_engine(alias, url)
            logger.info("Loaded dynamic DB '%s' from registry", alias)
        except Exception as exc:
            logger.warning("Could not load dynamic DB '%s': %s", alias, exc)

    env_aliases = settings.get_db_aliases()
    dyn_only = [a for a in dynamic_db_aliases() if a not in env_aliases]
    for alias in env_aliases + dyn_only:
        try:
            if is_collection_empty(alias):
                logger.info("Chroma collection empty for '%s' — running initial indexing…", alias)
                engine = get_engine(alias)
                tables = await introspect_schema(engine)
                index_tables(tables, alias)
                logger.info("Indexed %d tables for '%s'", len(tables), alias)
        except Exception as exc:
            logger.warning("Could not auto-index '%s': %s", alias, exc)
    yield


app = FastAPI(title="SpeakQL", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@app.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query(request: Request, body: QueryRequest = Body()) -> QueryResponse:
    question = body.question[:500].strip()
    db_alias = body.db_alias

    engine = get_engine(db_alias)
    db_url = settings.get_db_url(db_alias) if db_alias in settings.get_db_aliases() else (dynamic_db_aliases().get(db_alias) or "")
    dialect = detect_dialect(db_url)

    table_names = retrieve_tables(question, db_alias, top_k=settings.top_k_tables)
    if not table_names:
        return QueryResponse(
            question=question,
            clarify=True,
            clarify_message=(
                "I couldn't find tables related to your question. "
                "Try rephrasing or ask about a different topic."
            ),
        )

    all_tables = await introspect_schema(engine)
    table_map = {t.name: t for t in all_tables}
    relevant_tables = [table_map[n] for n in table_names if n in table_map]

    agent_result = await generate_sql(question, relevant_tables, dialect=dialect)

    if agent_result.clarify:
        return QueryResponse(
            question=question,
            clarify=True,
            clarify_message=agent_result.clarify_message,
            reasoning_trace=agent_result.reasoning_trace,
        )

    raw_sql = agent_result.sql or ""

    try:
        columns, rows, elapsed_ms = await execute_query(raw_sql, engine)
    except SQLValidationError:
        return QueryResponse(
            question=question,
            sql=raw_sql,
            error="The generated query looked unsafe and was blocked. Try a different question.",
            reasoning_trace=agent_result.reasoning_trace,
        )
    except QueryTimeoutError as exc:
        return QueryResponse(
            question=question,
            sql=raw_sql,
            error=str(exc),
            reasoning_trace=agent_result.reasoning_trace,
        )
    except QueryExecutionError as exc:
        return QueryResponse(
            question=question,
            sql=raw_sql,
            error=f"Something went wrong running the query. Here's the technical detail: {exc}",
            reasoning_trace=agent_result.reasoning_trace,
        )

    formatted_sql = format_sql(raw_sql, dialect=dialect)

    return QueryResponse(
        question=question,
        sql=formatted_sql,
        execution_time_ms=elapsed_ms,
        row_count=len(rows),
        columns=columns,
        rows=rows,
        clarify=False,
        reasoning_trace=agent_result.reasoning_trace,
    )


@app.get("/schema", response_model=SchemaResponse)
async def get_schema(db_alias: str = "default") -> SchemaResponse:
    engine = get_engine(db_alias)
    tables = await introspect_schema(engine)
    return SchemaResponse(db_alias=db_alias, tables=tables)


@app.post("/refresh-schema", response_model=RefreshResponse)
async def refresh_schema(db_alias: str = "default") -> RefreshResponse:
    engine = get_engine(db_alias)
    tables = await introspect_schema(engine)
    index_tables(tables, db_alias)
    return RefreshResponse(
        db_alias=db_alias,
        tables_indexed=len(tables),
        message=f"Re-indexed {len(tables)} tables for '{db_alias}'.",
    )


@app.get("/databases", response_model=DatabaseListResponse)
async def list_databases() -> DatabaseListResponse:
    dyn = dynamic_db_aliases()

    entries: list[tuple[str, str, str]] = []
    for alias in settings.get_db_aliases():
        try:
            url = settings.get_db_url(alias)
            entries.append((alias, url, "env"))
        except Exception:
            pass
    for alias, url in dyn.items():
        if alias not in settings.get_db_aliases():
            source = "upload" if "uploads" in url else "dynamic"
            entries.append((alias, url, source))

    databases: list[DatabaseInfo] = []
    for alias, url, source in entries:
        try:
            engine = get_engine(alias)
            table_names = await _get_table_names(engine)
            databases.append(DatabaseInfo(
                alias=alias,
                dialect=detect_dialect(url),
                table_count=len(table_names),
                tables=table_names,
                source=source,
            ))
        except Exception as exc:
            logger.warning("Could not list tables for '%s': %s", alias, exc)
            databases.append(DatabaseInfo(
                alias=alias,
                dialect=detect_dialect(url),
                table_count=0,
                tables=[],
                source=source,
            ))

    return DatabaseListResponse(databases=databases)


def _host_url(url: str) -> str:
    """Replace localhost/127.0.0.1 with host.docker.internal so the backend
    container can reach services running on the host machine."""
    return url.replace("localhost", "host.docker.internal").replace(
        "127.0.0.1", "host.docker.internal"
    )


@app.get("/databases/{alias}/suggestions")
async def database_suggestions(alias: str) -> dict:
    cached = get_suggestions(alias)
    if cached is not None:
        return {"alias": alias, "suggestions": cached}

    try:
        engine = get_engine(alias)
        tables = await introspect_schema(engine)
        questions = await generate_suggestions(tables)
        set_suggestions(alias, questions)
        return {"alias": alias, "suggestions": questions}
    except Exception as exc:
        logger.warning("Could not generate suggestions for '%s': %s", alias, exc)
        return {"alias": alias, "suggestions": []}


@app.get("/databases/{alias}/kpis")
async def database_kpis(alias: str) -> dict:
    cached = get_kpis(alias)
    if cached is not None:
        return {"alias": alias, "kpis": cached}

    try:
        engine = get_engine(alias)
        tables = await introspect_schema(engine)
        kpis = await compute_kpis(engine, tables)
        set_kpis(alias, kpis)
        return {"alias": alias, "kpis": kpis}
    except Exception as exc:
        logger.warning("Could not compute KPIs for '%s': %s", alias, exc)
        return {"alias": alias, "kpis": []}


@app.delete("/databases/{alias}")
async def delete_database(alias: str) -> dict:
    if alias in settings.get_db_aliases():
        raise HTTPException(status_code=403, detail=f"'{alias}' is a built-in database and cannot be deleted.")

    dyn = dynamic_db_aliases()
    if alias not in dyn:
        raise HTTPException(status_code=404, detail=f"Database '{alias}' not found.")

    url = dyn[alias]

    # Remove from registry and engine cache
    registry_deregister(alias)
    remove_engine(alias)

    # Delete the SQLite file if it was an upload
    if "uploads" in url:
        (UPLOADS_DIR / f"{alias}.db").unlink(missing_ok=True)

    # Remove Chroma index and cached metadata
    delete_index(alias)
    remove_suggestions(alias)
    remove_kpis(alias)

    return {"alias": alias, "deleted": True}


@app.post("/databases/connect", response_model=ConnectResponse)
async def connect_database(body: ConnectRequest) -> ConnectResponse:
    alias = body.alias.strip().lower().replace(" ", "_")
    if not alias:
        raise HTTPException(status_code=400, detail="Alias cannot be empty")

    url = _host_url(body.url.strip())
    engine = register_engine(alias, url)
    try:
        tables = await introspect_schema(engine)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not connect to database: {exc}")

    registry_register(alias, url)
    index_tables(tables, alias)

    return ConnectResponse(
        alias=alias,
        tables_indexed=len(tables),
        message=f"Connected '{alias}' — {len(tables)} tables indexed.",
    )


def _clean_name(s: str) -> str:
    return s.replace(" ", "_").replace("-", "_").lower()


@app.post("/databases/upload", response_model=ConnectResponse)
async def upload_database(file: UploadFile, alias: str = Form(...)) -> ConnectResponse:
    alias = _clean_name(alias.strip())
    if not alias:
        raise HTTPException(status_code=400, detail="Alias cannot be empty")

    suffix = Path(file.filename or "").suffix.lower()
    SUPPORTED = {".csv", ".tsv", ".xlsx", ".xls", ".json", ".parquet", ".db", ".sqlite", ".sql"}
    if suffix not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Accepted: {', '.join(sorted(SUPPORTED))}",
        )

    content = await file.read()
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    db_path = UPLOADS_DIR / f"{alias}.db"

    if suffix in (".db", ".sqlite"):
        db_path.write_bytes(content)

    elif suffix == ".sql":
        sql_text = content.decode("utf-8", errors="replace")
        con = sqlite3.connect(str(db_path))
        try:
            con.executescript(sql_text)
            con.commit()
        except Exception as exc:
            con.close()
            db_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"Could not execute SQL: {exc}")
        finally:
            con.close()

    else:
        import pandas as pd

        stem = _clean_name(Path(file.filename or alias).stem)
        con = sqlite3.connect(str(db_path))
        try:
            if suffix == ".csv":
                pd.read_csv(io.BytesIO(content)).to_sql(stem, con, if_exists="replace", index=False)
            elif suffix == ".tsv":
                pd.read_csv(io.BytesIO(content), sep="\t").to_sql(stem, con, if_exists="replace", index=False)
            elif suffix in (".xlsx", ".xls"):
                xf = pd.ExcelFile(io.BytesIO(content))
                for sheet in xf.sheet_names:
                    xf.parse(sheet).to_sql(_clean_name(sheet), con, if_exists="replace", index=False)
            elif suffix == ".json":
                try:
                    df = pd.read_json(io.BytesIO(content))
                except Exception:
                    import json
                    raw = json.loads(content)
                    df = pd.json_normalize(raw if isinstance(raw, list) else [raw])
                df.to_sql(stem, con, if_exists="replace", index=False)
            elif suffix == ".parquet":
                pd.read_parquet(io.BytesIO(content)).to_sql(stem, con, if_exists="replace", index=False)
        except Exception as exc:
            con.close()
            db_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}")
        finally:
            con.close()

    db_url = f"sqlite+aiosqlite:////app/uploads/{alias}.db"
    engine = register_engine(alias, db_url)
    registry_register(alias, db_url)

    try:
        tables = await introspect_schema(engine)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File saved but introspection failed: {exc}")

    index_tables(tables, alias)

    # Generate and cache suggestions + KPIs for this database
    try:
        questions = await generate_suggestions(tables)
        if questions:
            set_suggestions(alias, questions)
    except Exception as exc:
        logger.warning("Could not generate suggestions for '%s': %s", alias, exc)

    try:
        kpis = await compute_kpis(engine, tables)
        if kpis:
            set_kpis(alias, kpis)
    except Exception as exc:
        logger.warning("Could not compute KPIs for '%s': %s", alias, exc)

    return ConnectResponse(
        alias=alias,
        tables_indexed=len(tables),
        message=f"Uploaded '{alias}' — {len(tables)} tables indexed.",
    )


# Serve the built React frontend — only present inside the Docker image.
# API routes above take priority; this catches everything else (SPA routing).
_frontend = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend.exists():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
