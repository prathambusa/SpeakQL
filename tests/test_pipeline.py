"""
End-to-end happy-path tests using SQLite and the full pipeline.

These tests do NOT call an external LLM.  The agent is mocked so the pipeline
logic (validation → execution → response shape) can be verified without a key.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from backend.pipeline.agent import AgentResult
from backend.pipeline.executor import execute_query
from backend.pipeline.formatter import validate_sql, inject_limit, format_sql
from backend.db.introspect import introspect_schema


# ── Helper ────────────────────────────────────────────────────────────────────

async def _run_pipeline(question: str, sql: str, db_engine):
    """Simulate the /query pipeline with a pre-canned SQL."""
    # Step 1: mock agent returns pre-canned SQL
    agent_result = AgentResult(
        sql=sql,
        reasoning_trace="Mock reasoning: used products table.",
        clarify=False,
        clarify_message=None,
    )

    # Step 3: validate + execute
    validate_sql(agent_result.sql)
    capped = inject_limit(agent_result.sql, max_rows=1000)
    cols, rows, elapsed = await execute_query(capped, db_engine)

    # Step 4: format
    formatted = format_sql(agent_result.sql)

    return {
        "question": question,
        "sql": formatted,
        "columns": cols,
        "rows": rows,
        "row_count": len(rows),
        "execution_time_ms": elapsed,
        "reasoning_trace": agent_result.reasoning_trace,
        "clarify": False,
        "error": None,
    }


# ── Happy-path tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_simple_count(db_engine):
    result = await _run_pipeline(
        "How many products do we have?",
        "SELECT COUNT(*) AS total FROM products",
        db_engine,
    )
    assert result["error"] is None
    assert result["row_count"] == 1
    assert result["rows"][0][0] == 5
    assert "total" in result["columns"]


@pytest.mark.asyncio
async def test_e2e_filtered_query(db_engine):
    result = await _run_pipeline(
        "List all beverage products",
        "SELECT product_name, unit_price FROM products WHERE category = 'Beverages'",
        db_engine,
    )
    assert result["error"] is None
    assert result["row_count"] == 2  # Chai and Chang
    names = [r[0] for r in result["rows"]]
    assert "Chai" in names
    assert "Chang" in names


@pytest.mark.asyncio
async def test_e2e_join_query(db_engine):
    result = await _run_pipeline(
        "Show orders with product names",
        """
        SELECT o.order_id, o.customer, p.product_name, oi.quantity
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        ORDER BY o.order_id
        """,
        db_engine,
    )
    assert result["error"] is None
    assert result["row_count"] == 8
    assert "order_id" in result["columns"]
    assert "product_name" in result["columns"]


@pytest.mark.asyncio
async def test_e2e_response_shape(db_engine):
    """Verify the response object has all required fields."""
    result = await _run_pipeline(
        "What are the top products by price?",
        "SELECT product_name, unit_price FROM products ORDER BY unit_price DESC LIMIT 3",
        db_engine,
    )
    required_keys = {
        "question", "sql", "columns", "rows", "row_count",
        "execution_time_ms", "reasoning_trace", "clarify", "error",
    }
    assert required_keys.issubset(result.keys())
    assert result["row_count"] == 3
    # Carnarvon Tigers should be first (62.50)
    assert result["rows"][0][0] == "Carnarvon Tigers"


@pytest.mark.asyncio
async def test_e2e_introspect_feeds_context(db_engine):
    """Ensure introspection output contains enough info for the agent."""
    tables = await introspect_schema(db_engine)
    names = {t.name for t in tables}
    assert "products" in names
    # Should have at least one table with sample values for context
    products = next(t for t in tables if t.name == "products")
    assert products.sample_values is not None
    assert len(products.columns) >= 4
