from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from maze_pdf import presets as presets_mod
from maze_pdf.generator import ALGORITHMS, Maze, generate_with
from maze_pdf.opener import open_file
from maze_pdf.renderer import PageInfo, render_to_pdf

_MENU_KEY_TO_DIFFICULTY = {"1": "simple", "2": "medium", "3": "complex"}
MAX_PAGES = 10


def _ensure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, io.UnsupportedOperation):
            pass


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="laberinto",
        description="Genera laberintos imprimibles en PDF.",
    )
    parser.add_argument(
        "--difficulty",
        choices=["simple", "medium", "complex"],
        help="Dificultad a generar (salta el menú interactivo).",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Ancho en celdas (override de --difficulty). Requiere también --height.",
    )
    parser.add_argument(
        "--height",
        type=int,
        help="Alto en celdas (override de --difficulty). Requiere también --width.",
    )
    parser.add_argument("--output", type=Path, help="Ruta del PDF de salida.")
    parser.add_argument("--seed", type=int, help="Semilla para generación reproducible.")
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help=f"Número de páginas (laberintos) a generar. Entero 1-{MAX_PAGES}. Default: 1.",
    )
    parser.add_argument(
        "--algorithm",
        choices=list(ALGORITHMS),
        default="dfs",
        help="Algoritmo de generación. dfs (default): pasillos largos. prim: más bifurcaciones.",
    )
    parser.add_argument(
        "--show-solution",
        action="store_true",
        help="Dibuja el camino de la solución (entrada → salida) en rojo sobre el laberinto.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="No abrir el PDF automáticamente al terminar.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Ruta alternativa del archivo de configuración de presets.",
    )
    return parser


def _print_menu(current: dict[str, int]) -> None:
    print()
    print("=== Generador de Laberintos ===")
    for idx, key in enumerate(presets_mod.PRESET_KEYS, start=1):
        label = presets_mod.DISPLAY_LABELS[key]
        n = current[key]
        print(f"  {idx}) {label:<10}({n} x {n})")
    print("  4) Editar dificultades")
    print("  5) Salir")


def _prompt(message: str) -> str:
    return input(message)


def _edit_presets_flow(current: dict[str, int], config_path: Path | None) -> dict[str, int]:
    print()
    print("--- Editar dificultades ---")
    print("(Enter vacío = mantener valor actual)")
    updated = dict(current)
    for key in presets_mod.PRESET_KEYS:
        label = presets_mod.DISPLAY_LABELS[key]
        while True:
            raw = _prompt(f"  {label} [{updated[key]}]: ").strip()
            if raw == "":
                break
            try:
                n = int(raw)
            except ValueError:
                print("  Debe ser un entero >= 2. Intenta de nuevo.", file=sys.stderr)
                continue
            if n < 2:
                print("  Debe ser un entero >= 2. Intenta de nuevo.", file=sys.stderr)
                continue
            updated[key] = n
            break

    try:
        presets_mod.save_presets(updated, config_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return current

    print("Dificultades actualizadas.")
    return updated


def _prompt_page_count(default: int = 1, maximum: int = MAX_PAGES) -> int:
    while True:
        raw = _prompt(
            f"Número de páginas [1-{maximum}, default {default}]: "
        ).strip()
        if raw == "":
            return default
        try:
            n = int(raw)
        except ValueError:
            print(
                f"  Debe ser un entero entre 1 y {maximum}. Intenta de nuevo.",
                file=sys.stderr,
            )
            continue
        if n < 1 or n > maximum:
            print(
                f"  Debe ser un entero entre 1 y {maximum}. Intenta de nuevo.",
                file=sys.stderr,
            )
            continue
        return n


def _interactive_loop(
    current: dict[str, int], config_path: Path | None
) -> tuple[str, int, dict[str, int]] | None:
    while True:
        _print_menu(current)
        choice = _prompt("Elige una opción: ").strip()

        if choice in _MENU_KEY_TO_DIFFICULTY:
            difficulty = _MENU_KEY_TO_DIFFICULTY[choice]
            pages = _prompt_page_count()
            return difficulty, pages, current
        if choice == "4":
            current = _edit_presets_flow(current, config_path)
            continue
        if choice == "5":
            return None
        print("Opción no válida.", file=sys.stderr)


def _default_output_path(label: str, pages: int) -> Path:
    suffix = f"_{pages}p" if pages > 1 else ""
    return Path.cwd() / f"laberinto_{label}{suffix}.pdf"


def _build_mazes(
    width: int,
    height: int,
    pages: int,
    seed: int | None,
    algorithm: str,
) -> list[Maze]:
    if seed is None:
        return [generate_with(algorithm, width, height, seed=None) for _ in range(pages)]
    return [generate_with(algorithm, width, height, seed=seed + i) for i in range(pages)]


def _generate_and_render(
    *,
    width: int,
    height: int,
    pages: int,
    output: Path | None,
    seed: int | None,
    open_after: bool,
    algorithm: str,
    show_solution: bool,
    difficulty_label: str | None,
) -> int:
    # Etiqueta para nombre de archivo y para el header del PDF.
    if difficulty_label:
        file_label = difficulty_label
        header_difficulty = difficulty_label
    else:
        file_label = f"{width}x{height}"
        header_difficulty = "Personalizado"

    out_path = (output or _default_output_path(file_label, pages)).resolve()

    mazes = _build_mazes(width, height, pages, seed, algorithm)
    page_infos = [
        PageInfo(difficulty=header_difficulty, seed=(seed + i) if seed is not None else None)
        for i in range(pages)
    ]
    render_to_pdf(
        mazes,
        out_path,
        show_solution=show_solution,
        page_infos=page_infos,
        title=f"Laberinto {header_difficulty} {width}x{height}",
    )

    suffix = f" ({pages} páginas)" if pages > 1 else ""
    solution_note = "  [con solución]" if show_solution else ""
    print(f"PDF generado{suffix}: {out_path}{solution_note}")

    if open_after:
        open_file(out_path)

    return 0


def _validate_custom_dims(args: argparse.Namespace) -> tuple[int, int] | None:
    """Si --width y --height ambos presentes, valida y retorna (w, h).
    Si solo uno, error. Si ninguno, None."""
    if args.width is None and args.height is None:
        return None
    if args.width is None or args.height is None:
        raise ValueError("--width y --height deben usarse juntos")
    if args.width < 2 or args.height < 2:
        raise ValueError("--width y --height deben ser >= 2")
    return args.width, args.height


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_console()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.pages < 1 or args.pages > MAX_PAGES:
        print(
            f"error: --pages debe ser un entero entre 1 y {MAX_PAGES}; "
            f"se recibió {args.pages}.",
            file=sys.stderr,
        )
        return 2

    try:
        current = presets_mod.load_presets(args.config)
        custom_dims = _validate_custom_dims(args)

        # Camino scripteado: si hay --difficulty o dimensiones custom, saltamos el menú.
        if args.difficulty or custom_dims is not None:
            if custom_dims is not None:
                width, height = custom_dims
                difficulty_label = args.difficulty or None
            else:
                n = presets_mod.resolve(current, args.difficulty)
                width, height = n, n
                difficulty_label = presets_mod.DISPLAY_LABELS.get(
                    args.difficulty, args.difficulty
                )
            return _generate_and_render(
                width=width,
                height=height,
                pages=args.pages,
                output=args.output,
                seed=args.seed,
                open_after=not args.no_open,
                algorithm=args.algorithm,
                show_solution=args.show_solution,
                difficulty_label=difficulty_label,
            )

        try:
            result = _interactive_loop(current, args.config)
        except (KeyboardInterrupt, EOFError):
            print()
            return 130

        if result is None:
            return 0

        difficulty, pages, current = result
        n = presets_mod.resolve(current, difficulty)
        return _generate_and_render(
            width=n,
            height=n,
            pages=pages,
            output=args.output,
            seed=args.seed,
            open_after=not args.no_open,
            algorithm=args.algorithm,
            show_solution=args.show_solution,
            difficulty_label=presets_mod.DISPLAY_LABELS.get(difficulty, difficulty),
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error inesperado: {exc}", file=sys.stderr)
        return 1
