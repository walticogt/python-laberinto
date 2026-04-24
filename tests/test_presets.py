from __future__ import annotations

import json
from pathlib import Path

import pytest

from maze_pdf import presets as presets_mod


def test_missing_config_returns_defaults(tmp_path: Path) -> None:
    path = tmp_path / "nope.json"
    assert presets_mod.load_presets(path) == presets_mod.DEFAULT_PRESETS


def test_malformed_json_falls_back(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{ this is not json", encoding="utf-8")

    result = presets_mod.load_presets(path)

    assert result == presets_mod.DEFAULT_PRESETS
    captured = capsys.readouterr()
    assert "warning" in captured.err.lower()


def test_partial_config_merges_defaults(tmp_path: Path) -> None:
    path = tmp_path / "partial.json"
    path.write_text(json.dumps({"presets": {"simple": 7}}), encoding="utf-8")

    result = presets_mod.load_presets(path)

    assert result == {
        "simple": 7,
        "medium": presets_mod.DEFAULT_PRESETS["medium"],
        "complex": presets_mod.DEFAULT_PRESETS["complex"],
    }


def test_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "cfg.json"
    original = {"simple": 12, "medium": 22, "complex": 33}
    presets_mod.save_presets(original, path)

    assert presets_mod.load_presets(path) == original


def test_save_rejects_too_small(tmp_path: Path) -> None:
    path = tmp_path / "cfg.json"
    with pytest.raises(ValueError, match="simple"):
        presets_mod.save_presets({"simple": 1, "medium": 20, "complex": 40}, path)
    assert not path.exists()


def test_save_rejects_non_integer(tmp_path: Path) -> None:
    path = tmp_path / "cfg.json"
    with pytest.raises(ValueError, match="simple"):
        presets_mod.save_presets(
            {"simple": "fifteen", "medium": 20, "complex": 40},  # type: ignore[dict-item]
            path,
        )


def test_save_rejects_missing_key(tmp_path: Path) -> None:
    path = tmp_path / "cfg.json"
    with pytest.raises(ValueError, match="complex"):
        presets_mod.save_presets({"simple": 10, "medium": 20}, path)  # type: ignore[arg-type]


def test_save_warns_on_large_preset(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "cfg.json"
    presets_mod.save_presets({"simple": 15, "medium": 25, "complex": 80}, path)
    captured = capsys.readouterr()
    assert "complex" in captured.err
    assert "80" in captured.err


def test_resolve_unknown_name_raises() -> None:
    with pytest.raises(ValueError, match="dificultad"):
        presets_mod.resolve(presets_mod.DEFAULT_PRESETS, "imposible")
