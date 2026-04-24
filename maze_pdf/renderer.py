from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from maze_pdf.generator import Maze, solve

_VALID_PAGE_SIZES = {"a4", "letter"}
_MARGIN_MM = 15.0
_HEADER_MARGIN_MM = 8.0          # espacio extra reservado arriba para el título
_MM_PER_PT = 0.352777778
_MM_PER_INCH = 25.4
_HEADER_FONT_SIZE_PT = 9
_SOLUTION_COLOR = (0.90, 0.17, 0.17)  # rojo intenso en RGB 0..1


@dataclass(frozen=True)
class PageInfo:
    """Metadatos opcionales para imprimir en el encabezado de cada página."""

    difficulty: str | None = None
    seed: int | None = None


def _page_size_mm(name: str) -> tuple[float, float]:
    if name == "a4":
        return (210.0, 297.0)
    if name == "letter":
        return (8.5 * _MM_PER_INCH, 11.0 * _MM_PER_INCH)
    raise ValueError(f"page_size inválido: {name!r}. Opciones: a4, letter")


def _line_weight_pt(n: int) -> tuple[float, bool]:
    if n <= 25:
        return 0.75, False
    if n <= 40:
        return 0.5, False
    if n <= 60:
        return 0.4, False
    return 0.3, True


def compute_cell_size_mm(width: int, height: int, page_size: str) -> float:
    page_w_mm, page_h_mm = _page_size_mm(page_size)
    usable_w = page_w_mm - 2 * _MARGIN_MM
    # El header consume un poco de espacio vertical para el texto.
    usable_h = page_h_mm - 2 * _MARGIN_MM - _HEADER_MARGIN_MM
    return min(usable_w / width, usable_h / height)


def _draw_header(c, page_w_pt: float, page_h_pt: float, text: str) -> None:
    c.saveState()
    c.setFont("Helvetica", _HEADER_FONT_SIZE_PT)
    c.setFillGray(0.25)
    margin_pt = _MARGIN_MM / _MM_PER_PT
    # Posición Y: alineado con el borde superior del laberinto, un poco arriba.
    y = page_h_pt - margin_pt + 2
    c.drawString(margin_pt, y, text)
    c.restoreState()


def _draw_maze(
    c,
    maze: Maze,
    page_w_pt: float,
    page_h_pt: float,
    page_size: str,
    show_solution: bool,
) -> None:
    n_max = max(maze.width, maze.height)
    line_weight, warn = _line_weight_pt(n_max)
    if warn:
        print(
            f"warning: N={n_max} excede 60; las líneas a {line_weight}pt pueden "
            f"imprimirse demasiado finas.",
            file=sys.stderr,
        )

    cell_mm = compute_cell_size_mm(maze.width, maze.height, page_size)
    cell_pt = cell_mm / _MM_PER_PT

    maze_w_pt = maze.width * cell_pt
    maze_h_pt = maze.height * cell_pt
    origin_x_pt = (page_w_pt - maze_w_pt) / 2
    # Shift vertical hacia abajo para dejar espacio al header arriba.
    header_shift_pt = (_HEADER_MARGIN_MM / _MM_PER_PT) / 2
    origin_y_pt = (page_h_pt - maze_h_pt) / 2 - header_shift_pt

    c.saveState()
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(line_weight)
    c.setLineCap(0)

    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.cells[y][x]
            left = origin_x_pt + x * cell_pt
            right = left + cell_pt
            top = origin_y_pt + (maze.height - y) * cell_pt
            bottom = top - cell_pt

            if cell.north:
                c.line(left, top, right, top)
            if cell.west:
                c.line(left, bottom, left, top)
            if y == maze.height - 1 and cell.south:
                c.line(left, bottom, right, bottom)
            if x == maze.width - 1 and cell.east:
                c.line(right, bottom, right, top)
    c.restoreState()

    if show_solution:
        path = solve(maze)
        if len(path) >= 2:
            c.saveState()
            c.setStrokeColorRGB(*_SOLUTION_COLOR)
            solution_weight = max(line_weight * 2.2, 1.0)
            c.setLineWidth(solution_weight)
            c.setLineCap(1)  # round
            c.setLineJoin(1)
            # La línea conecta los centros de las celdas.
            def cell_center_pt(cx: int, cy: int) -> tuple[float, float]:
                px = origin_x_pt + cx * cell_pt + cell_pt / 2
                py = origin_y_pt + (maze.height - cy) * cell_pt - cell_pt / 2
                return px, py

            # Extender la línea hacia afuera en entrada y salida (a través del hueco).
            # Entrada: arriba-izq, hueco N → subir cell_pt/2 extra.
            # Salida:  abajo-der, hueco S → bajar cell_pt/2 extra.
            entry_center = cell_center_pt(*maze.entry)
            exit_center = cell_center_pt(*maze.exit)
            entry_outside = (entry_center[0], entry_center[1] + cell_pt / 2)
            exit_outside = (exit_center[0], exit_center[1] - cell_pt / 2)

            p = c.beginPath()
            p.moveTo(*entry_outside)
            for cx, cy in path:
                p.lineTo(*cell_center_pt(cx, cy))
            p.lineTo(*exit_outside)
            c.drawPath(p, stroke=1, fill=0)
            c.restoreState()


def render_to_pdf(
    mazes: Sequence[Maze],
    path: str | Path,
    page_size: str = "a4",
    *,
    show_solution: bool = False,
    page_infos: Sequence[PageInfo] | None = None,
    title: str | None = None,
) -> None:
    if page_size not in _VALID_PAGE_SIZES:
        raise ValueError(
            f"page_size inválido: {page_size!r}. Opciones: {sorted(_VALID_PAGE_SIZES)}"
        )
    if len(mazes) == 0:
        raise ValueError("mazes debe contener al menos un laberinto")
    if page_infos is not None and len(page_infos) != len(mazes):
        raise ValueError(
            f"page_infos debe tener la misma longitud que mazes "
            f"({len(page_infos)} vs {len(mazes)})"
        )

    from reportlab.lib.pagesizes import A4, LETTER
    from reportlab.pdfgen import canvas

    page_dims = A4 if page_size == "a4" else LETTER
    page_w_pt, page_h_pt = page_dims

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_path), pagesize=page_dims)
    c.setTitle(title or "Generador de Laberintos")
    c.setAuthor("maze-pdf")
    c.setSubject("Laberinto imprimible generado por maze-pdf")
    c.setKeywords("maze,laberinto,dfs,pdf,generator")
    c.setCreator("maze-pdf (https://github.com/)")

    total = len(mazes)
    for i, maze in enumerate(mazes):
        info = page_infos[i] if page_infos else PageInfo()
        header = _format_header(i + 1, total, info, maze.width, maze.height)
        if header:
            _draw_header(c, page_w_pt, page_h_pt, header)
        _draw_maze(c, maze, page_w_pt, page_h_pt, page_size, show_solution)
        c.showPage()
    c.save()


def _format_header(
    page_index: int,
    total_pages: int,
    info: PageInfo,
    width: int,
    height: int,
) -> str:
    parts: list[str] = []
    if total_pages > 1:
        parts.append(f"Laberinto {page_index}/{total_pages}")
    else:
        parts.append("Laberinto")
    if info.difficulty:
        parts.append(info.difficulty.capitalize())
    parts.append(f"{width}x{height}")
    if info.seed is not None:
        parts.append(f"seed {info.seed}")
    return "  ·  ".join(parts)
