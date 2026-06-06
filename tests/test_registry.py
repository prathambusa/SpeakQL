"""Unit tests for backend/db/registry.py — file I/O is isolated via monkeypatching."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch


def _make_registry(tmp_path: Path):
    """Import a fresh copy of the registry module with all paths redirected to tmp_path."""
    import importlib
    import backend.db.registry as reg

    reg._registry = {}
    reg._suggestions = {}
    reg._kpis = {}
    reg.REGISTRY_FILE = tmp_path / "dynamic_dbs.json"
    reg.SUGGESTIONS_FILE = tmp_path / "suggestions.json"
    reg.KPIS_FILE = tmp_path / "kpis.json"
    return reg


def test_register_and_get_url(tmp_path):
    reg = _make_registry(tmp_path)
    reg.register("mydb", "sqlite:///test.db")
    assert reg.get_url("mydb") == "sqlite:///test.db"


def test_register_persists_to_file(tmp_path):
    reg = _make_registry(tmp_path)
    reg.register("mydb", "sqlite:///test.db")
    saved = json.loads(reg.REGISTRY_FILE.read_text())
    assert saved["mydb"] == "sqlite:///test.db"


def test_all_aliases_returns_copy(tmp_path):
    reg = _make_registry(tmp_path)
    reg.register("a", "sqlite:///a.db")
    reg.register("b", "sqlite:///b.db")
    aliases = reg.all_aliases()
    assert set(aliases.keys()) == {"a", "b"}
    aliases["c"] = "sqlite:///c.db"
    assert "c" not in reg.all_aliases()


def test_deregister_removes_alias(tmp_path):
    reg = _make_registry(tmp_path)
    reg.register("mydb", "sqlite:///test.db")
    reg.deregister("mydb")
    assert reg.get_url("mydb") is None


def test_deregister_nonexistent_is_safe(tmp_path):
    reg = _make_registry(tmp_path)
    reg.deregister("nope")  # should not raise


def test_load_reads_existing_files(tmp_path):
    reg = _make_registry(tmp_path)
    reg.REGISTRY_FILE.write_text(json.dumps({"x": "sqlite:///x.db"}))
    reg.SUGGESTIONS_FILE.write_text(json.dumps({"x": ["Q1?", "Q2?"]}))
    reg.KPIS_FILE.write_text(json.dumps({"x": [{"label": "Total", "value": "5"}]}))

    reg.load()
    assert reg.get_url("x") == "sqlite:///x.db"
    assert reg.get_suggestions("x") == ["Q1?", "Q2?"]
    assert reg.get_kpis("x")[0]["label"] == "Total"


def test_load_tolerates_corrupt_files(tmp_path):
    reg = _make_registry(tmp_path)
    reg.REGISTRY_FILE.write_text("{bad json")
    reg.SUGGESTIONS_FILE.write_text("{bad json")
    reg.KPIS_FILE.write_text("{bad json")
    reg.load()
    assert reg.all_aliases() == {}


def test_set_and_get_suggestions(tmp_path):
    reg = _make_registry(tmp_path)
    reg.set_suggestions("db1", ["How much revenue?", "Top customers?"])
    assert reg.get_suggestions("db1") == ["How much revenue?", "Top customers?"]


def test_suggestions_persisted_to_file(tmp_path):
    reg = _make_registry(tmp_path)
    reg.set_suggestions("db1", ["Q1?"])
    saved = json.loads(reg.SUGGESTIONS_FILE.read_text())
    assert saved["db1"] == ["Q1?"]


def test_remove_suggestions(tmp_path):
    reg = _make_registry(tmp_path)
    reg.set_suggestions("db1", ["Q1?"])
    reg.remove_suggestions("db1")
    assert reg.get_suggestions("db1") is None


def test_remove_suggestions_nonexistent_is_safe(tmp_path):
    reg = _make_registry(tmp_path)
    reg.remove_suggestions("nope")


def test_set_and_get_kpis(tmp_path):
    reg = _make_registry(tmp_path)
    kpis = [{"label": "Revenue", "value": "$1.2M", "sub": None}]
    reg.set_kpis("db1", kpis)
    assert reg.get_kpis("db1") == kpis


def test_kpis_persisted_to_file(tmp_path):
    reg = _make_registry(tmp_path)
    kpis = [{"label": "Revenue", "value": "$1.2M", "sub": None}]
    reg.set_kpis("db1", kpis)
    saved = json.loads(reg.KPIS_FILE.read_text())
    assert saved["db1"][0]["label"] == "Revenue"


def test_remove_kpis(tmp_path):
    reg = _make_registry(tmp_path)
    reg.set_kpis("db1", [{"label": "X", "value": "1", "sub": None}])
    reg.remove_kpis("db1")
    assert reg.get_kpis("db1") is None


def test_remove_kpis_nonexistent_is_safe(tmp_path):
    reg = _make_registry(tmp_path)
    reg.remove_kpis("nope")


def test_get_url_missing_returns_none(tmp_path):
    reg = _make_registry(tmp_path)
    assert reg.get_url("missing") is None


def test_get_suggestions_missing_returns_none(tmp_path):
    reg = _make_registry(tmp_path)
    assert reg.get_suggestions("missing") is None


def test_get_kpis_missing_returns_none(tmp_path):
    reg = _make_registry(tmp_path)
    assert reg.get_kpis("missing") is None
