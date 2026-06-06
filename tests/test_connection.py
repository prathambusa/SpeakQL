"""Unit tests for backend/db/connection.py — URL normalisation and engine cache."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from backend.db.connection import _normalise_url, register_engine, remove_engine, _engine_cache


# ── URL normalisation ─────────────────────────────────────────────────────────

def test_normalise_bare_sqlite():
    assert _normalise_url("sqlite:///foo.db") == "sqlite+aiosqlite:///foo.db"


def test_normalise_sqlite_already_async():
    url = "sqlite+aiosqlite:///foo.db"
    assert _normalise_url(url) == url


def test_normalise_postgresql_scheme():
    assert _normalise_url("postgresql://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"


def test_normalise_postgres_alias():
    assert _normalise_url("postgres://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"


def test_normalise_postgresql_already_async():
    url = "postgresql+asyncpg://u:p@host/db"
    assert _normalise_url(url) == url


def test_normalise_unknown_scheme_passthrough():
    url = "mssql+aioodbc://u:p@host/db"
    assert _normalise_url(url) == url


# ── Engine cache ──────────────────────────────────────────────────────────────

def test_register_engine_stores_in_cache():
    alias = "_test_cache_alias"
    remove_engine(alias)  # clean slate
    engine = register_engine(alias, "sqlite+aiosqlite:///:memory:")
    assert _engine_cache.get(alias) is engine
    remove_engine(alias)


def test_register_engine_returns_engine():
    alias = "_test_return_alias"
    remove_engine(alias)
    engine = register_engine(alias, "sqlite+aiosqlite:///:memory:")
    assert engine is not None
    remove_engine(alias)


def test_remove_engine_clears_cache():
    alias = "_test_remove_alias"
    register_engine(alias, "sqlite+aiosqlite:///:memory:")
    assert alias in _engine_cache
    remove_engine(alias)
    assert alias not in _engine_cache


def test_remove_engine_missing_is_safe():
    remove_engine("__definitely_not_registered__")


def test_get_engine_uses_cache(monkeypatch):
    """get_engine should return the cached engine without hitting settings again."""
    from backend.db.connection import get_engine

    alias = "_test_get_cached"
    remove_engine(alias)
    expected = register_engine(alias, "sqlite+aiosqlite:///:memory:")

    # If cache is used, settings.get_db_url should never be called
    with patch("backend.config.settings.get_db_url", side_effect=AssertionError("should not call settings")):
        result = get_engine(alias)

    assert result is expected
    remove_engine(alias)


def test_get_engine_unknown_alias_raises():
    from backend.db.connection import get_engine
    import backend.db.registry as reg

    alias = "__totally_unknown_alias_xyz__"
    remove_engine(alias)
    old_url = reg.get_url(alias)

    with pytest.raises(ValueError, match="Unknown database alias"):
        get_engine(alias)
