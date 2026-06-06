"""FastAPI integration tests — no real LLM, no real Chroma, no real databases."""
from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from backend.pipeline.agent import AgentResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_agent(sql: str = "SELECT 1", clarify: bool = False):
    return AsyncMock(return_value=AgentResult(
        sql=sql,
        reasoning_trace="mock trace",
        clarify=clarify,
        clarify_message="Need more info" if clarify else None,
    ))


def _mock_retrieve(table_names: list[str] = ["products"]):
    return MagicMock(return_value=table_names)


@pytest_asyncio.fixture()
async def client(db_engine):
    """ASGI test client wired to the real FastAPI app, but with external I/O mocked."""
    from backend.main import app

    with (
        patch("backend.main.get_engine", return_value=db_engine),
        patch("backend.main.is_collection_empty", return_value=False),
        patch("backend.main.load_registry"),
        patch("backend.main.dynamic_db_aliases", return_value={}),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac


# ── /health ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── /query ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_query_returns_results(client, db_engine):
    with (
        patch("backend.main.retrieve_tables", _mock_retrieve(["products"])),
        patch("backend.main.introspect_schema", AsyncMock(return_value=[])),
        patch("backend.main.generate_sql", _mock_agent("SELECT product_id, product_name FROM products")),
        patch("backend.main.get_engine", return_value=db_engine),
    ):
        response = await client.post("/query", json={"question": "List products", "db_alias": "default"})

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "List products"
    assert body["columns"] is not None
    assert body["rows"] is not None


@pytest.mark.asyncio
async def test_query_no_tables_returns_clarify(client, db_engine):
    with (
        patch("backend.main.retrieve_tables", _mock_retrieve([])),
        patch("backend.main.get_engine", return_value=db_engine),
    ):
        response = await client.post("/query", json={"question": "huh?", "db_alias": "default"})

    assert response.status_code == 200
    body = response.json()
    assert body["clarify"] is True


@pytest.mark.asyncio
async def test_query_agent_clarify_propagated(client, db_engine):
    with (
        patch("backend.main.retrieve_tables", _mock_retrieve(["products"])),
        patch("backend.main.introspect_schema", AsyncMock(return_value=[])),
        patch("backend.main.generate_sql", _mock_agent(clarify=True)),
        patch("backend.main.get_engine", return_value=db_engine),
    ):
        response = await client.post("/query", json={"question": "ambiguous?", "db_alias": "default"})

    assert response.status_code == 200
    body = response.json()
    assert body["clarify"] is True
    assert body["clarify_message"] == "Need more info"


@pytest.mark.asyncio
async def test_query_missing_question_rejected(client):
    response = await client.post("/query", json={"db_alias": "default"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_query_empty_question_rejected(client):
    response = await client.post("/query", json={"question": "", "db_alias": "default"})
    assert response.status_code == 422


# ── /schema ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_schema_returns_tables(client, db_engine):
    with (
        patch("backend.main.get_engine", return_value=db_engine),
        patch("backend.main.introspect_schema") as mock_introspect,
    ):
        from backend.models import TableMeta, ColumnMeta
        mock_introspect.return_value = [
            TableMeta(name="products", columns=[ColumnMeta(name="product_id", type="INTEGER")])
        ]
        mock_introspect.__class__ = AsyncMock
        mock_introspect.side_effect = None
        mock_introspect.return_value = [
            TableMeta(name="products", columns=[ColumnMeta(name="product_id", type="INTEGER")])
        ]

        # Use AsyncMock for the coroutine
        with patch("backend.main.introspect_schema", AsyncMock(return_value=[
            TableMeta(name="products", columns=[ColumnMeta(name="product_id", type="INTEGER")])
        ])):
            response = await client.get("/schema?db_alias=default")

    assert response.status_code == 200
    body = response.json()
    assert body["db_alias"] == "default"
    assert isinstance(body["tables"], list)


# ── /databases ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_databases_returns_list(client):
    from backend.config import settings

    with (
        patch.object(settings, "get_db_aliases", return_value=[]),
        patch("backend.main.dynamic_db_aliases", return_value={}),
    ):
        response = await client.get("/databases")

    assert response.status_code == 200
    body = response.json()
    assert "databases" in body
    assert isinstance(body["databases"], list)


@pytest.mark.asyncio
async def test_delete_env_database_returns_403(client):
    from backend.config import settings

    with patch.object(settings, "get_db_aliases", return_value=["default"]):
        response = await client.delete("/databases/default")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_unknown_database_returns_404(client):
    from backend.config import settings

    with (
        patch.object(settings, "get_db_aliases", return_value=[]),
        patch("backend.main.dynamic_db_aliases", return_value={}),
    ):
        response = await client.delete("/databases/nonexistent_xyz")

    assert response.status_code == 404


# ── /databases/{alias}/kpis ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_kpis_endpoint_returns_cached(client):
    from backend.db import registry as reg
    reg.set_kpis("_test_alias", [{"label": "Revenue", "value": "$1M", "sub": None}])

    with patch("backend.main.get_kpis", return_value=[{"label": "Revenue", "value": "$1M", "sub": None}]):
        response = await client.get("/databases/_test_alias/kpis")

    assert response.status_code == 200
    body = response.json()
    assert "kpis" in body

    reg.remove_kpis("_test_alias")


# ── /databases/{alias}/suggestions ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_suggestions_endpoint_returns_cached(client):
    with patch("backend.main.get_suggestions", return_value=["Q1?", "Q2?", "Q3?"]):
        response = await client.get("/databases/_test_alias/suggestions")

    assert response.status_code == 200
    body = response.json()
    assert "suggestions" in body
    assert body["suggestions"] == ["Q1?", "Q2?", "Q3?"]
