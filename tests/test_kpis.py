"""Tests for KPI formatting helpers and compute_kpis with a mocked LLM."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.pipeline.kpis import (
    _fmt_currency,
    _fmt_number,
    _format_value,
    compute_kpis,
)


# ── _fmt_currency ─────────────────────────────────────────────────────────────

def test_fmt_currency_billions():
    assert _fmt_currency(2_500_000_000) == "$2.5B"


def test_fmt_currency_millions():
    assert _fmt_currency(1_200_000) == "$1.2M"


def test_fmt_currency_thousands():
    assert _fmt_currency(5_500) == "$6K"  # 5500/1000 = 5.5, rounds to 6 with :.0f


def test_fmt_currency_small():
    assert _fmt_currency(42.5) == "$42.50"


def test_fmt_currency_zero():
    assert _fmt_currency(0) == "$0.00"


# ── _fmt_number ───────────────────────────────────────────────────────────────

def test_fmt_number_billions():
    assert _fmt_number(3_000_000_000) == "3.0B"


def test_fmt_number_millions():
    assert _fmt_number(2_500_000) == "2.5M"


def test_fmt_number_thousands():
    assert _fmt_number(4_500) == "4.5K"


def test_fmt_number_integer():
    assert _fmt_number(42) == "42"


def test_fmt_number_float():
    assert _fmt_number(3.14) == "3.14"


def test_fmt_number_large_integer_with_comma():
    assert _fmt_number(1000) == "1.0K"


# ── _format_value ─────────────────────────────────────────────────────────────

def test_format_value_none_returns_dash():
    assert _format_value(None, "number") == "—"


def test_format_value_currency():
    assert _format_value(1_000_000, "currency") == "$1.0M"


def test_format_value_number():
    assert _format_value(42, "number") == "42"


def test_format_value_percent():
    assert _format_value(73.5, "percent") == "73.5%"


def test_format_value_text():
    assert _format_value("Alice", "text") == "Alice"


def test_format_value_text_truncated_at_32():
    long_str = "A" * 40
    assert len(_format_value(long_str, "text")) <= 32


def test_format_value_non_numeric_currency_falls_back_to_str():
    assert _format_value("N/A", "currency") == "N/A"


# ── compute_kpis with mocked LLM ─────────────────────────────────────────────

def _make_mock_llm(json_response: str):
    mock_msg = MagicMock()
    mock_msg.content = json_response

    mock_llm = MagicMock()
    mock_llm.bind.return_value = mock_llm
    mock_llm.ainvoke = AsyncMock(return_value=mock_msg)
    return mock_llm


@pytest.mark.asyncio
async def test_compute_kpis_returns_results(db_engine):
    kpi_json = """[
      {"label": "Total Products", "sql": "SELECT COUNT(*) FROM products", "unit": "number", "sub": "all SKUs"},
      {"label": "Avg Price",      "sql": "SELECT AVG(unit_price) FROM products", "unit": "currency", "sub": "mean unit price"},
      {"label": "Total Revenue",  "sql": "SELECT SUM(total) FROM orders", "unit": "currency", "sub": "all orders"},
      {"label": "Top Customer",   "sql": "SELECT customer FROM orders GROUP BY customer ORDER BY SUM(total) DESC LIMIT 1", "unit": "text", "sub": "by order value"}
    ]"""

    with patch("backend.pipeline.kpis._build_llm", return_value=_make_mock_llm(kpi_json)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        kpis = await compute_kpis(db_engine, tables)

    assert len(kpis) >= 3
    labels = {k["label"] for k in kpis}
    assert "Total Products" in labels


@pytest.mark.asyncio
async def test_compute_kpis_correct_values(db_engine):
    kpi_json = """[
      {"label": "Product Count", "sql": "SELECT COUNT(*) FROM products", "unit": "number", "sub": null},
      {"label": "Order Count",   "sql": "SELECT COUNT(*) FROM orders",   "unit": "number", "sub": null},
      {"label": "Total Revenue", "sql": "SELECT SUM(total) FROM orders", "unit": "currency", "sub": null},
      {"label": "Top Customer",  "sql": "SELECT customer FROM orders GROUP BY customer ORDER BY SUM(total) DESC LIMIT 1", "unit": "text", "sub": null}
    ]"""

    with patch("backend.pipeline.kpis._build_llm", return_value=_make_mock_llm(kpi_json)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        kpis = await compute_kpis(db_engine, tables)

    kpi_map = {k["label"]: k["value"] for k in kpis}
    assert kpi_map["Product Count"] == "5"
    assert kpi_map["Order Count"] == "5"
    assert kpi_map["Top Customer"] == "Charlie"  # Charlie: $125 single order > Alice's $117.50 across two


@pytest.mark.asyncio
async def test_compute_kpis_filters_non_select(db_engine):
    kpi_json = """[
      {"label": "Bad KPI",       "sql": "DROP TABLE products", "unit": "number", "sub": null},
      {"label": "Good KPI",      "sql": "SELECT COUNT(*) FROM products", "unit": "number", "sub": null},
      {"label": "Good KPI 2",    "sql": "SELECT COUNT(*) FROM orders", "unit": "number", "sub": null},
      {"label": "Good KPI 3",    "sql": "SELECT AVG(unit_price) FROM products", "unit": "currency", "sub": null}
    ]"""

    with patch("backend.pipeline.kpis._build_llm", return_value=_make_mock_llm(kpi_json)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        kpis = await compute_kpis(db_engine, tables)

    labels = {k["label"] for k in kpis}
    assert "Bad KPI" not in labels


@pytest.mark.asyncio
async def test_compute_kpis_uses_structural_fallback_when_llm_fails(db_engine):
    mock_llm = MagicMock()
    mock_llm.bind.return_value = mock_llm
    mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM unavailable"))

    with patch("backend.pipeline.kpis._build_llm", return_value=mock_llm):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        kpis = await compute_kpis(db_engine, tables)

    assert len(kpis) >= 1
    labels = {k["label"] for k in kpis}
    assert "Total Rows" in labels


@pytest.mark.asyncio
async def test_compute_kpis_returns_empty_for_no_tables(db_engine):
    kpis = await compute_kpis(db_engine, [])
    assert kpis == []


@pytest.mark.asyncio
async def test_compute_kpis_caps_at_four(db_engine):
    kpi_json = """[
      {"label": "KPI 1", "sql": "SELECT COUNT(*) FROM products", "unit": "number", "sub": null},
      {"label": "KPI 2", "sql": "SELECT COUNT(*) FROM orders",   "unit": "number", "sub": null},
      {"label": "KPI 3", "sql": "SELECT AVG(unit_price) FROM products", "unit": "currency", "sub": null},
      {"label": "KPI 4", "sql": "SELECT SUM(total) FROM orders", "unit": "currency", "sub": null}
    ]"""

    with patch("backend.pipeline.kpis._build_llm", return_value=_make_mock_llm(kpi_json)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        kpis = await compute_kpis(db_engine, tables)

    assert len(kpis) <= 4


@pytest.mark.asyncio
async def test_compute_kpis_skips_null_results(db_engine):
    # SQL that returns NULL
    kpi_json = """[
      {"label": "Bad Null", "sql": "SELECT NULL", "unit": "number", "sub": null},
      {"label": "Good",     "sql": "SELECT COUNT(*) FROM products", "unit": "number", "sub": null},
      {"label": "Good 2",   "sql": "SELECT COUNT(*) FROM orders", "unit": "number", "sub": null},
      {"label": "Good 3",   "sql": "SELECT AVG(unit_price) FROM products", "unit": "currency", "sub": null}
    ]"""

    with patch("backend.pipeline.kpis._build_llm", return_value=_make_mock_llm(kpi_json)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        kpis = await compute_kpis(db_engine, tables)

    labels = {k["label"] for k in kpis}
    assert "Bad Null" not in labels
