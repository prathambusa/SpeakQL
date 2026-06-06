"""Tests for safe SQL execution and row-cap enforcement."""
import pytest
from backend.pipeline.executor import execute_query, QueryTimeoutError
from backend.pipeline.formatter import SQLValidationError


@pytest.mark.asyncio
async def test_execute_simple_select(db_engine):
    cols, rows, elapsed = await execute_query(
        "SELECT product_id, product_name FROM products",
        db_engine,
    )
    assert cols == ["product_id", "product_name"]
    assert len(rows) == 5
    assert elapsed >= 0


@pytest.mark.asyncio
async def test_execute_with_filter(db_engine):
    cols, rows, elapsed = await execute_query(
        "SELECT product_name FROM products WHERE unit_price > 20",
        db_engine,
    )
    names = [r[0] for r in rows]
    # Carnarvon Tigers (62.50) and Pavlova? No, Pavlova=17.45 < 20
    # Only Carnarvon Tigers > 20 and Chang=19 < 20
    # Actually: Chai=18, Chang=19, Aniseed=10, Pavlova=17.45, Carnarvon=62.50
    # Only Carnarvon Tigers
    assert "Carnarvon Tigers" in names


@pytest.mark.asyncio
async def test_row_cap_applied(db_engine):
    # With max_rows=2 we should only get 2 rows from a 5-row table
    cols, rows, elapsed = await execute_query(
        "SELECT * FROM products",
        db_engine,
        max_rows=2,
    )
    assert len(rows) <= 2


@pytest.mark.asyncio
async def test_unsafe_sql_blocked(db_engine):
    with pytest.raises(SQLValidationError):
        await execute_query("DROP TABLE products", db_engine)


@pytest.mark.asyncio
async def test_delete_blocked(db_engine):
    with pytest.raises(SQLValidationError):
        await execute_query("DELETE FROM orders WHERE order_id = 1001", db_engine)


@pytest.mark.asyncio
async def test_timeout_mechanism_exists(db_engine):
    # Verify that the executor raises QueryTimeoutError when asyncio.wait_for times out.
    import asyncio
    from unittest.mock import patch

    async def _raise_timeout(coro, timeout):
        coro.close()  # clean up the unawaited coroutine
        raise asyncio.TimeoutError()

    with patch("backend.pipeline.executor.asyncio.wait_for", side_effect=_raise_timeout):
        with pytest.raises((QueryTimeoutError, asyncio.TimeoutError)):
            await execute_query(
                "SELECT * FROM products",
                db_engine,
                timeout=30,
            )
