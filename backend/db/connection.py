from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from backend.config import settings

_engine_cache: dict[str, AsyncEngine] = {}


def _normalise_url(url: str) -> str:
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://") and "+asyncpg" not in url:
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _make_engine(url: str) -> AsyncEngine:
    url = _normalise_url(url)
    kwargs: dict = {"echo": False}
    if "sqlite" in url:
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_async_engine(url, **kwargs)


def get_engine(db_alias: str) -> AsyncEngine:
    if db_alias in _engine_cache:
        return _engine_cache[db_alias]

    try:
        url = settings.get_db_url(db_alias)
    except ValueError:
        from backend.db.registry import get_url
        url = get_url(db_alias)
        if url is None:
            raise ValueError(f"Unknown database alias '{db_alias}'")

    engine = _make_engine(url)
    _engine_cache[db_alias] = engine
    return engine


def register_engine(alias: str, url: str) -> AsyncEngine:
    engine = _make_engine(url)
    _engine_cache[alias] = engine
    return engine


def remove_engine(alias: str) -> None:
    _engine_cache.pop(alias, None)
