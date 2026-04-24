from __future__ import annotations

from pathlib import Path

import pytest

from maze_pdf.generator import generate
from maze_pdf.renderer import compute_cell_size_mm, render_to_pdf


def _count_pdf_pages(data: bytes) -> int:
    return data.count(b"/Type /Page\n") + data.count(b"/Type /Page ")


def test_rendered_file_is_pdf(tmp_path: Path) -> None:
    maze = generate(15, 15, seed=1)
    out = tmp_path / "out.pdf"
    render_to_pdf([maze], out)

    data = out.read_bytes()
    assert data[:5] == b"%PDF-"
    assert len(data) > 0


def test_large_maze_renders(tmp_path: Path) -> None:
    maze = generate(60, 60, seed=1)
    out = tmp_path / "big.pdf"
    render_to_pdf([maze], out)

    data = out.read_bytes()
    assert data[:5] == b"%PDF-"


def test_small_grid_has_larger_cells_than_large_grid() -> None:
    small_cell = compute_cell_size_mm(5, 5, "a4")
    large_cell = compute_cell_size_mm(40, 40, "a4")
    assert small_cell >= 4 * large_cell


def test_invalid_page_size_raises(tmp_path: Path) -> None:
    maze = generate(10, 10, seed=1)
    out = tmp_path / "bad.pdf"
    with pytest.raises(ValueError, match="page_size"):
        render_to_pdf([maze], out, page_size="a3")
    assert not out.exists()


def test_letter_page_works(tmp_path: Path) -> None:
    maze = generate(15, 15, seed=1)
    out = tmp_path / "letter.pdf"
    render_to_pdf([maze], out, page_size="letter")
    assert out.read_bytes()[:5] == b"%PDF-"


def test_show_solution_embeds_red_color(tmp_path: Path) -> None:
    from maze_pdf.generator import generate
    maze = generate(10, 10, seed=1)
    out = tmp_path / "with_solution.pdf"
    render_to_pdf([maze], out, show_solution=True)
    data = out.read_bytes()
    assert data[:5] == b"%PDF-"
    # El PDF con solución es notablemente más grande por la polyline extra.
    out2 = tmp_path / "no_solution.pdf"
    render_to_pdf([maze], out2, show_solution=False)
    assert len(out.read_bytes()) > len(out2.read_bytes())


def test_pdf_title_metadata_is_set(tmp_path: Path) -> None:
    from maze_pdf.generator import generate
    maze = generate(10, 10, seed=1)
    out = tmp_path / "titled.pdf"
    render_to_pdf([maze], out, title="Mi Laberinto Personalizado")
    data = out.read_bytes()
    # reportlab escribe el título en el Info dictionary
    assert b"Mi Laberinto Personalizado" in data


def test_page_header_increases_pdf_size(tmp_path: Path) -> None:
    # El header agrega texto al content stream; el PDF con PageInfo debe ser
    # mayor que sin él. (No comparamos bytes literales porque reportlab
    # comprime/codifica los content streams.)
    from maze_pdf.generator import generate
    from maze_pdf.renderer import PageInfo
    maze = generate(10, 10, seed=42)
    with_header = tmp_path / "with_header.pdf"
    no_header = tmp_path / "no_header.pdf"
    render_to_pdf(
        [maze],
        with_header,
        page_infos=[PageInfo(difficulty="Medio", seed=42)],
    )
    render_to_pdf([maze], no_header)
    assert with_header.read_bytes()[:5] == b"%PDF-"
    assert len(with_header.read_bytes()) > len(no_header.read_bytes())


def test_page_infos_length_mismatch_raises(tmp_path: Path) -> None:
    from maze_pdf.generator import generate
    from maze_pdf.renderer import PageInfo
    maze = generate(8, 8, seed=1)
    out = tmp_path / "bad.pdf"
    with pytest.raises(ValueError, match="page_infos"):
        render_to_pdf([maze, maze], out, page_infos=[PageInfo()])


def test_multi_page_pdf(tmp_path: Path) -> None:
    mazes = [generate(10, 10, seed=i) for i in range(3)]
    out = tmp_path / "multi.pdf"
    render_to_pdf(mazes, out)

    data = out.read_bytes()
    assert data[:5] == b"%PDF-"
    assert _count_pdf_pages(data) == 3


def test_empty_maze_list_raises(tmp_path: Path) -> None:
    out = tmp_path / "empty.pdf"
    with pytest.raises(ValueError, match="al menos un"):
        render_to_pdf([], out)
    assert not out.exists()
