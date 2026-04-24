from __future__ import annotations

import json
from pathlib import Path

import pytest

from maze_pdf import cli as cli_mod


def _count_pdf_pages(data: bytes) -> int:
    return data.count(b"/Type /Page\n") + data.count(b"/Type /Page ")


def test_scripted_run_writes_pdf_and_skips_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[Path] = []

    def _fake_open(path: Path) -> bool:
        opened.append(path)
        return True

    monkeypatch.setattr(cli_mod, "open_file", _fake_open)

    out = tmp_path / "scripted.pdf"
    cfg = tmp_path / "cfg.json"

    rc = cli_mod.main(
        [
            "--difficulty",
            "simple",
            "--output",
            str(out),
            "--seed",
            "1",
            "--no-open",
            "--config",
            str(cfg),
        ]
    )

    assert rc == 0
    assert out.read_bytes()[:5] == b"%PDF-"
    assert opened == []


def test_invalid_difficulty_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli_mod.main(["--difficulty", "impossible"])
    assert excinfo.value.code != 0
    err = capsys.readouterr().err
    assert "impossible" in err or "invalid choice" in err


def test_opener_failure_is_non_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _raising_open(path: Path) -> bool:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_mod, "open_file", _raising_open)

    out = tmp_path / "o.pdf"
    cfg = tmp_path / "cfg.json"

    rc = cli_mod.main(
        [
            "--difficulty",
            "simple",
            "--output",
            str(out),
            "--seed",
            "1",
            "--config",
            str(cfg),
        ]
    )

    assert rc != 0 or out.exists()
    captured = capsys.readouterr()
    assert str(out.resolve()) in captured.out


def test_edit_flow_via_stdin_updates_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "cfg.json"

    script = iter(["4", "10", "", "50", "5"])

    def _fake_input(prompt: str = "") -> str:
        return next(script)

    monkeypatch.setattr(cli_mod, "_prompt", _fake_input)

    rc = cli_mod.main(["--config", str(cfg)])
    assert rc == 0

    saved = json.loads(cfg.read_text(encoding="utf-8"))
    assert saved["presets"]["simple"] == 10
    assert saved["presets"]["medium"] == 25
    assert saved["presets"]["complex"] == 50


def test_menu_displays_current_preset_sizes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = tmp_path / "cfg.json"
    cfg.write_text(
        json.dumps({"presets": {"simple": 8, "medium": 20, "complex": 50}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(cli_mod, "_prompt", lambda _="": "5")

    rc = cli_mod.main(["--config", str(cfg)])
    assert rc == 0

    out = capsys.readouterr().out
    assert "Básico" in out and "(8 x 8)" in out
    assert "Medio" in out and "(20 x 20)" in out
    assert "Complejo" in out and "(50 x 50)" in out


def test_pages_flag_produces_multi_page_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_mod, "open_file", lambda _: True)

    out = tmp_path / "multi.pdf"
    cfg = tmp_path / "cfg.json"

    rc = cli_mod.main(
        [
            "--difficulty",
            "simple",
            "--pages",
            "4",
            "--seed",
            "1",
            "--no-open",
            "--output",
            str(out),
            "--config",
            str(cfg),
        ]
    )

    assert rc == 0
    data = out.read_bytes()
    assert data[:5] == b"%PDF-"
    assert _count_pdf_pages(data) == 4


@pytest.mark.parametrize("bad", ["0", "11", "-1", "100"])
def test_invalid_pages_flag_exits_nonzero(
    bad: str, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    cfg = tmp_path / "cfg.json"
    rc = cli_mod.main(
        [
            "--difficulty",
            "simple",
            "--pages",
            bad,
            "--config",
            str(cfg),
            "--no-open",
        ]
    )
    assert rc != 0
    assert "--pages" in capsys.readouterr().err


def test_build_mazes_seed_is_deterministic() -> None:
    a = cli_mod._build_mazes(width=10, height=10, pages=3, seed=42, algorithm="dfs")
    b = cli_mod._build_mazes(width=10, height=10, pages=3, seed=42, algorithm="dfs")
    assert len(a) == 3 and len(b) == 3
    for ma, mb in zip(a, b):
        for y in range(ma.height):
            for x in range(ma.width):
                ca, cb = ma.cells[y][x], mb.cells[y][x]
                assert (ca.north, ca.south, ca.east, ca.west) == (
                    cb.north,
                    cb.south,
                    cb.east,
                    cb.west,
                )


def test_build_mazes_with_seed_produces_different_mazes_per_page() -> None:
    mazes = cli_mod._build_mazes(width=10, height=10, pages=3, seed=42, algorithm="dfs")
    structures = set()
    for m in mazes:
        key = tuple(
            (c.north, c.south, c.east, c.west)
            for row in m.cells
            for c in row
        )
        structures.add(key)
    assert len(structures) == 3


def test_interactive_page_prompt_produces_multi_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_mod, "open_file", lambda _: True)

    script = iter(["1", "3"])

    def _fake_input(prompt: str = "") -> str:
        return next(script)

    monkeypatch.setattr(cli_mod, "_prompt", _fake_input)

    out = tmp_path / "inter.pdf"
    cfg = tmp_path / "cfg.json"
    rc = cli_mod.main(
        [
            "--output",
            str(out),
            "--seed",
            "7",
            "--no-open",
            "--config",
            str(cfg),
        ]
    )

    assert rc == 0
    data = out.read_bytes()
    assert _count_pdf_pages(data) == 3


def test_interactive_page_prompt_blank_defaults_to_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_mod, "open_file", lambda _: True)

    script = iter(["2", ""])

    def _fake_input(prompt: str = "") -> str:
        return next(script)

    monkeypatch.setattr(cli_mod, "_prompt", _fake_input)

    out = tmp_path / "inter.pdf"
    cfg = tmp_path / "cfg.json"
    rc = cli_mod.main(
        [
            "--output",
            str(out),
            "--seed",
            "7",
            "--no-open",
            "--config",
            str(cfg),
        ]
    )

    assert rc == 0
    assert _count_pdf_pages(out.read_bytes()) == 1


def test_custom_width_height_bypasses_difficulty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_mod, "open_file", lambda _: True)
    out = tmp_path / "custom.pdf"
    cfg = tmp_path / "cfg.json"
    rc = cli_mod.main(
        [
            "--width", "12", "--height", "7",
            "--seed", "1", "--no-open",
            "--output", str(out), "--config", str(cfg),
        ]
    )
    assert rc == 0
    assert out.read_bytes()[:5] == b"%PDF-"


def test_width_without_height_errors(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.json"
    rc = cli_mod.main(
        ["--width", "10", "--config", str(cfg), "--no-open"]
    )
    assert rc == 2  # ValueError from _validate_custom_dims


def test_show_solution_flag_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_mod, "open_file", lambda _: True)
    out = tmp_path / "solved.pdf"
    cfg = tmp_path / "cfg.json"
    rc = cli_mod.main(
        [
            "--difficulty", "simple",
            "--seed", "1",
            "--show-solution",
            "--no-open",
            "--output", str(out),
            "--config", str(cfg),
        ]
    )
    assert rc == 0
    assert out.read_bytes()[:5] == b"%PDF-"


def test_prim_algorithm_flag_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_mod, "open_file", lambda _: True)
    out = tmp_path / "prim.pdf"
    cfg = tmp_path / "cfg.json"
    rc = cli_mod.main(
        [
            "--difficulty", "simple",
            "--algorithm", "prim",
            "--seed", "1",
            "--no-open",
            "--output", str(out),
            "--config", str(cfg),
        ]
    )
    assert rc == 0
    assert out.read_bytes()[:5] == b"%PDF-"


def test_interactive_page_prompt_rejects_invalid_then_accepts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_mod, "open_file", lambda _: True)

    script = iter(["1", "abc", "0", "11", "2"])

    def _fake_input(prompt: str = "") -> str:
        return next(script)

    monkeypatch.setattr(cli_mod, "_prompt", _fake_input)

    out = tmp_path / "inter.pdf"
    cfg = tmp_path / "cfg.json"
    rc = cli_mod.main(
        [
            "--output",
            str(out),
            "--seed",
            "7",
            "--no-open",
            "--config",
            str(cfg),
        ]
    )

    assert rc == 0
    assert _count_pdf_pages(out.read_bytes()) == 2
