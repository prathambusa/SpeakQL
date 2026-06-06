from __future__ import annotations

import json
import logging
import re

from backend.db.introspect import table_to_document
from backend.models import TableMeta
from backend.pipeline.agent import _build_llm

logger = logging.getLogger(__name__)

_PROMPT = """\
You are a data analyst. Given the following database schema (with sample values), \
generate exactly 3 specific, interesting questions that a non-technical business user \
would want to ask about this data.

Rules:
- Each question MUST reference actual table or column names visible in the schema.
- Questions must be answerable with a SELECT query.
- Sound natural and business-relevant — not technical or generic.
- Do NOT ask "how many rows", "list all tables", or other structural questions.

Schema:
{schema}

Respond with ONLY a JSON array of exactly 3 question strings. No markdown, no explanation.
Example: ["Question one?", "Question two?", "Question three?"]
"""


async def generate_suggestions(tables: list[TableMeta]) -> list[str]:
    if not tables:
        return []

    # Cap schema size to avoid huge prompts
    schema_text = "\n\n".join(table_to_document(t) for t in tables[:8])

    from langchain_core.messages import HumanMessage

    llm = _build_llm()
    # Lean on a small token budget — we only need 3 short questions
    llm = llm.bind(max_tokens=512)

    try:
        response = await llm.ainvoke([HumanMessage(content=_PROMPT.format(schema=schema_text))])
        raw: str = response.content if hasattr(response, "content") else str(response)

        # Strip markdown fences if the model wrapped the JSON
        raw = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip().strip("`").strip()

        questions = json.loads(raw)
        if isinstance(questions, list):
            return [q for q in questions if isinstance(q, str)][:3]
    except Exception as exc:
        logger.warning("Could not generate suggestions: %s", exc)

    return []
