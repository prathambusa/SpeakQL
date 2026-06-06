"""Tests for generate_suggestions with mocked LLM."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.pipeline.suggestions import generate_suggestions


def _make_mock_llm(json_response: str):
    mock_msg = MagicMock()
    mock_msg.content = json_response

    mock_llm = MagicMock()
    mock_llm.bind.return_value = mock_llm
    mock_llm.ainvoke = AsyncMock(return_value=mock_msg)
    return mock_llm


@pytest.mark.asyncio
async def test_generate_suggestions_returns_three(db_engine):
    llm_output = '["Which products are most popular?", "Who are the top customers?", "What is total revenue?"]'

    with patch("backend.pipeline.suggestions._build_llm", return_value=_make_mock_llm(llm_output)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        questions = await generate_suggestions(tables)

    assert len(questions) == 3
    assert all(isinstance(q, str) for q in questions)


@pytest.mark.asyncio
async def test_generate_suggestions_strips_markdown_fences(db_engine):
    llm_output = '```json\n["Q1?", "Q2?", "Q3?"]\n```'

    with patch("backend.pipeline.suggestions._build_llm", return_value=_make_mock_llm(llm_output)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        questions = await generate_suggestions(tables)

    assert questions == ["Q1?", "Q2?", "Q3?"]


@pytest.mark.asyncio
async def test_generate_suggestions_caps_at_three(db_engine):
    llm_output = '["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]'

    with patch("backend.pipeline.suggestions._build_llm", return_value=_make_mock_llm(llm_output)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        questions = await generate_suggestions(tables)

    assert len(questions) <= 3


@pytest.mark.asyncio
async def test_generate_suggestions_llm_failure_returns_empty(db_engine):
    mock_llm = MagicMock()
    mock_llm.bind.return_value = mock_llm
    mock_llm.ainvoke = AsyncMock(side_effect=Exception("network error"))

    with patch("backend.pipeline.suggestions._build_llm", return_value=mock_llm):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        questions = await generate_suggestions(tables)

    assert questions == []


@pytest.mark.asyncio
async def test_generate_suggestions_invalid_json_returns_empty(db_engine):
    with patch("backend.pipeline.suggestions._build_llm", return_value=_make_mock_llm("{not valid json")):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        questions = await generate_suggestions(tables)

    assert questions == []


@pytest.mark.asyncio
async def test_generate_suggestions_empty_tables_returns_empty():
    questions = await generate_suggestions([])
    assert questions == []


@pytest.mark.asyncio
async def test_generate_suggestions_filters_non_strings(db_engine):
    llm_output = '["Q1?", 42, null, "Q2?", "Q3?"]'

    with patch("backend.pipeline.suggestions._build_llm", return_value=_make_mock_llm(llm_output)):
        from backend.db.introspect import introspect_schema
        tables = await introspect_schema(db_engine)
        questions = await generate_suggestions(tables)

    assert all(isinstance(q, str) for q in questions)
