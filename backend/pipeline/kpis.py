from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.db.introspect import table_to_document
from backend.models import TableMeta
from backend.pipeline.agent import _build_llm

logger = logging.getLogger(__name__)

_PROMPT = """\
You are a data analyst. Given the database schema below (with sample values), \
generate exactly 4 KPI definitions that give a meaningful snapshot of what's in the data.

Rules:
- KPIs must reflect the CONTENT of the data — totals, averages, top items, rates, counts of real entities
- Do NOT use row counts, table counts, or structural metadata as KPIs
- Each KPI needs a SQLite-compatible SELECT that returns exactly ONE scalar value
- Choose the right unit: "number" for counts/years/IDs, "currency" for money, \
  "percent" for 0-100 ratios, "text" for string answers (names, categories)
- A column named "year", "id", "code" is NEVER currency — use "number" or "text"
- Labels must be short and human-friendly (e.g. "Total Revenue", "Top Country", "Win Rate")
- You MUST return exactly 4 items. If data is limited, be creative but stay accurate.

Schema (with sample values):
{schema}

Return ONLY a JSON array, no markdown:
[
  {{"label": "...", "sql": "SELECT ...", "unit": "number|currency|percent|text", "sub": "brief context"}},
  ...
]
"""


async def _scalar(engine: AsyncEngine, sql: str, params: dict | None = None) -> Any:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(sql), params or {})
            row = result.fetchone()
            return row[0] if row else None
    except Exception as exc:
        logger.debug("KPI query failed (%s): %s", exc, sql[:120])
        return None


def _fmt_currency(n: float) -> str:
    if n >= 1_000_000_000:
        return f"${n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n / 1_000:.0f}K"
    return f"${n:,.2f}"


def _format_value(raw: Any, unit: str) -> str:
    if raw is None:
        return "—"
    try:
        if unit == "currency":
            return _fmt_currency(float(raw))
        if unit == "number":
            return _fmt_number(float(raw))
        if unit == "percent":
            return f"{float(raw):.1f}%"
    except (ValueError, TypeError):
        pass
    return str(raw)[:32]


async def _generate_kpi_defs(tables: list[TableMeta]) -> list[dict]:
    schema = "\n\n".join(table_to_document(t) for t in tables[:8])

    from langchain_core.messages import HumanMessage
    llm = _build_llm()
    llm = llm.bind(max_tokens=768)

    try:
        response = await llm.ainvoke([HumanMessage(content=_PROMPT.format(schema=schema))])
        raw: str = response.content if hasattr(response, "content") else str(response)
        raw = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip().strip("`").strip()
        defs = json.loads(raw)
        if isinstance(defs, list):
            return [d for d in defs if isinstance(d, dict) and "label" in d and "sql" in d]
    except Exception as exc:
        logger.warning("KPI definition generation failed: %s", exc)

    return []


def _fmt_number(n: float) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{int(n):,}" if n == int(n) else f"{n:,.2f}"


async def _structural_fallbacks(engine: AsyncEngine, tables: list[TableMeta]) -> list[dict]:
    """Minimal always-available KPIs used only if LLM returns too few results."""
    fallbacks = []
    total_rows = sum(t.row_count or 0 for t in tables)
    fallbacks.append({"label": "Total Rows", "value": _fmt_number(total_rows), "sub": None})
    if len(tables) > 1:
        biggest = max(tables, key=lambda t: t.row_count or 0)
        fallbacks.append({"label": "Largest Table", "value": biggest.name,
                          "sub": f"{_fmt_number(biggest.row_count or 0)} rows"})
    return fallbacks


async def compute_kpis(engine: AsyncEngine, tables: list[TableMeta]) -> list[dict]:
    if not tables:
        return []

    kpi_defs = await _generate_kpi_defs(tables)

    results: list[dict] = []
    for kpi in kpi_defs[:4]:
        sql = kpi.get("sql", "").strip()
        if not sql.upper().startswith("SELECT"):
            continue
        raw = await _scalar(engine, sql)
        if raw is None:
            continue
        results.append({
            "label": kpi.get("label", ""),
            "value": _format_value(raw, kpi.get("unit", "text")),
            "sub": kpi.get("sub") or None,
        })

    # Guarantee at least 3 KPIs
    if len(results) < 3:
        for fb in await _structural_fallbacks(engine, tables):
            if len(results) >= 3:
                break
            if not any(r["label"] == fb["label"] for r in results):
                results.append(fb)

    return results[:4]
