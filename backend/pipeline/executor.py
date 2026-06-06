from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.config import settings
from backend.pipeline.formatter import SQLValidationError, inject_limit, validate_sql

logger = logging.getLogger(__name__)


class QueryTimeoutError(Exception):
    pass


class QueryExecutionError(Exception):
    pass


async def _run_query(engine: AsyncEngine, sql: str) -> tuple[list[str], list[list[Any]]]:
    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        return columns, rows


async def execute_query(
    sql: str,
    engine: AsyncEngine,
    timeout: int | None = None,
    max_rows: int | None = None,
) -> tuple[list[str], list[list[Any]], float]:
    """
    Validate, cap, and execute a SQL query.

    Returns (columns, rows, execution_time_ms).
    Raises SQLValidationError, QueryTimeoutError, or QueryExecutionError.
    """
    t_out = timeout or settings.query_timeout_seconds
    m_rows = max_rows or settings.max_rows

    validate_sql(sql)
    capped_sql = inject_limit(sql, m_rows)

    start = time.perf_counter()
    try:
        columns, rows = await asyncio.wait_for(
            _run_query(engine, capped_sql),
            timeout=float(t_out),
        )
    except asyncio.TimeoutError:
        raise QueryTimeoutError(
            f"The query took longer than {t_out} seconds. Try a more specific question."
        )
    except SQLValidationError:
        raise
    except Exception as exc:
        logger.exception("DB execution error")
        raise QueryExecutionError(str(exc)) from exc

    elapsed_ms = (time.perf_counter() - start) * 1000

    # Serialise non-JSON-safe values (dates, Decimals, etc.)
    serialised_rows = _serialise_rows(rows)

    return columns, serialised_rows, round(elapsed_ms, 2)


def _serialise_rows(rows: list[list[Any]]) -> list[list[Any]]:
    import datetime
    import decimal

    def _convert(v: Any) -> Any:
        if isinstance(v, (datetime.date, datetime.datetime)):
            return v.isoformat()
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, bytes):
            return v.decode("utf-8", errors="replace")
        return v

    return [[_convert(cell) for cell in row] for row in rows]
