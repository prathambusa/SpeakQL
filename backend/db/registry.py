from __future__ import annotations

import json
from pathlib import Path

_BASE = Path(__file__).parent.parent

REGISTRY_FILE    = _BASE / "dynamic_dbs.json"
SUGGESTIONS_FILE = _BASE / "suggestions.json"
KPIS_FILE        = _BASE / "kpis.json"

_registry:    dict[str, str]        = {}
_suggestions: dict[str, list[str]]  = {}
_kpis:        dict[str, list[dict]] = {}


def load() -> None:
    global _registry, _suggestions, _kpis
    if REGISTRY_FILE.exists():
        try:
            _registry = json.loads(REGISTRY_FILE.read_text())
        except Exception:
            _registry = {}
    if SUGGESTIONS_FILE.exists():
        try:
            _suggestions = json.loads(SUGGESTIONS_FILE.read_text())
        except Exception:
            _suggestions = {}
    if KPIS_FILE.exists():
        try:
            _kpis = json.loads(KPIS_FILE.read_text())
        except Exception:
            _kpis = {}


def save() -> None:
    REGISTRY_FILE.write_text(json.dumps(_registry, indent=2))


def register(alias: str, url: str) -> None:
    _registry[alias] = url
    save()


def get_url(alias: str) -> str | None:
    return _registry.get(alias)


def all_aliases() -> dict[str, str]:
    return dict(_registry)


def deregister(alias: str) -> None:
    _registry.pop(alias, None)
    save()


def set_suggestions(alias: str, questions: list[str]) -> None:
    _suggestions[alias] = questions
    SUGGESTIONS_FILE.write_text(json.dumps(_suggestions, indent=2))


def get_suggestions(alias: str) -> list[str] | None:
    return _suggestions.get(alias)


def remove_suggestions(alias: str) -> None:
    if alias in _suggestions:
        del _suggestions[alias]
        SUGGESTIONS_FILE.write_text(json.dumps(_suggestions, indent=2))


def set_kpis(alias: str, kpis: list[dict]) -> None:
    _kpis[alias] = kpis
    KPIS_FILE.write_text(json.dumps(_kpis, indent=2))


def get_kpis(alias: str) -> list[dict] | None:
    return _kpis.get(alias)


def remove_kpis(alias: str) -> None:
    if alias in _kpis:
        del _kpis[alias]
        KPIS_FILE.write_text(json.dumps(_kpis, indent=2))
