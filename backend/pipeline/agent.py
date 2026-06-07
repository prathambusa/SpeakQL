from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

from backend.config import settings
from backend.models import TableMeta
from backend.db.introspect import table_to_document

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """\
You are SpeakQL, an expert SQL assistant. Your job is to convert a natural-language \
question into a single, correct SQL query for the database described below.

## Database Dialect
{dialect}

## Available Tables
{schema}

## Strict Rules
- Generate ONLY a SELECT statement. NEVER use DROP, DELETE, UPDATE, INSERT, \
TRUNCATE, ALTER, CREATE, EXEC, EXECUTE, or any DDL/DML.
- Use ONLY the tables and columns listed in the schema above. Do not invent tables.
- If you are unsure or the question cannot be answered from the available tables, \
respond ONLY with a JSON clarification (see Response Format below).
- Do not add SQL fences (```), backticks, or explanatory text after the SQL.

## Response Format
Step 1 — think step-by-step inside <thinking>…</thinking> tags.
Step 2a — if you can answer: output ONLY the raw SQL query (no fences, no prose).
Step 2b — if the question is ambiguous or unanswerable: output ONLY this JSON object:
{{"clarify": true, "message": "<plain-English explanation of what you need>"}}
"""

_HUMAN_TEMPLATE = "Question: {question}"


# ── Output parsing ─────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    sql: Optional[str]
    reasoning_trace: Optional[str]
    clarify: bool
    clarify_message: Optional[str]


def _parse_output(raw: str) -> AgentResult:
    # Extract reasoning
    reasoning: str | None = None
    thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw, re.DOTALL | re.IGNORECASE)
    if thinking_match:
        reasoning = thinking_match.group(1).strip()
        # Strip thinking block from the remainder
        raw_remainder = raw[thinking_match.end():].strip()
    else:
        raw_remainder = raw.strip()

    # Try clarify JSON
    json_match = re.search(r"\{[^{}]*\"clarify\"\s*:\s*true[^{}]*\}", raw_remainder, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if data.get("clarify"):
                return AgentResult(
                    sql=None,
                    reasoning_trace=reasoning,
                    clarify=True,
                    clarify_message=data.get("message", "Please clarify your question."),
                )
        except json.JSONDecodeError:
            pass

    # Strip any stray markdown fences
    raw_remainder = re.sub(r"```(?:sql)?", "", raw_remainder, flags=re.IGNORECASE).strip()
    raw_remainder = raw_remainder.strip("`").strip()

    # Match CTEs (WITH <name> AS ...) or plain SELECT queries
    select_match = re.search(
        r"(WITH\s+\w+\s+AS\s*\(.*|SELECT\b.*)",
        raw_remainder, re.DOTALL | re.IGNORECASE,
    )
    if select_match:
        sql = select_match.group(1).strip()
        return AgentResult(sql=sql, reasoning_trace=reasoning, clarify=False, clarify_message=None)

    # Nothing usable
    return AgentResult(
        sql=None,
        reasoning_trace=reasoning,
        clarify=True,
        clarify_message="Could not produce a SQL query for this question. Try rephrasing.",
    )


# ── LLM factory ───────────────────────────────────────────────────────────────

def _build_llm():
    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic  # lazy import
        return ChatAnthropic(
            model=settings.claude_model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0,
            max_tokens=4096,
        )
    elif settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI  # lazy import
        return ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=0,
        )
    raise RuntimeError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")


# ── Public API ─────────────────────────────────────────────────────────────────

async def generate_sql(
    question: str,
    tables: list[TableMeta],
    dialect: str = "sqlite",
) -> AgentResult:
    """
    Call the LLM to generate SQL for `question` given the retrieved `tables`.
    Returns an AgentResult with sql, reasoning_trace, or clarify fields set.
    """
    if not tables:
        return AgentResult(
            sql=None,
            reasoning_trace=None,
            clarify=True,
            clarify_message=(
                "I couldn't find tables related to your question. "
                "Try rephrasing or ask about a different topic."
            ),
        )

    schema_text = "\n\n".join(table_to_document(t) for t in tables)
    system_prompt = _SYSTEM_TEMPLATE.format(dialect=dialect, schema=schema_text)

    from langchain_core.messages import SystemMessage, HumanMessage  # lazy import

    llm = _build_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=_HUMAN_TEMPLATE.format(question=question)),
    ]

    try:
        response = await llm.ainvoke(messages)
        raw: str = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.exception("LLM call failed")
        return AgentResult(
            sql=None,
            reasoning_trace=None,
            clarify=True,
            clarify_message=f"Couldn't generate a query right now. ({exc})",
        )

    result = _parse_output(raw)
    logger.debug("Agent result: clarify=%s sql=%s", result.clarify, result.sql)
    return result
