## Why

The project currently has no functional code. The owner wants a standalone tool that produces printable maze puzzles on demand — something friends/family/students can generate without needing to know anything about maze algorithms. A PDF output (rather than on-screen) is the target because the mazes are intended to be printed and solved on paper, and PDF is the universal printable format.

## What Changes

- Introduce a Python 3 application with a text-based CLI menu as the entry point.
- The menu lets the user pick a difficulty (`Básico` / `Medio` / `Complejo`) and triggers maze generation.
- A maze-generation engine produces a perfect (single-solution) maze whose size scales with difficulty.
- A PDF renderer writes the maze to a file on disk, always fitting a single page: **larger grid → smaller cells, smaller grid → bigger cells**, so any difficulty fits one printable sheet regardless of size.
- The menu offers a dedicated option to **edit the difficulty presets** (default `básico=15`, `medio=25`, `complejo=40`); edits persist to a JSON config file and survive across runs.
- After writing the PDF, the tool **automatically opens it with the OS default application** (browser/PDF viewer). A `--no-open` flag disables this for scripted use.
- The user can ask for **multiple mazes in a single PDF** (one per page) — after choosing a difficulty, the menu prompts for a page count (**default 1, max 10**). A `--pages N` flag enables the same for scripted use. Each page is a different maze of the same difficulty; when a `--seed` is provided, successive pages use `seed, seed+1, …` so the output stays reproducible.
- Ship a minimal `pyproject.toml` / `requirements.txt` so the tool can be installed and run with `python -m maze_pdf` or a console script.

Non-goals for this change (may become future proposals):
- Circular or themed mazes (like the reference images with "Apple" decoration).
- Graphical UI (Tkinter/web). CLI only for now.
- Solution-path overlay, timing, or interactive solving.

## Capabilities

### New Capabilities

- `maze-generation`: Produce a rectangular perfect-maze grid of a requested size using a randomized algorithm, returning a data structure that downstream renderers can consume.
- `pdf-rendering`: Render a maze data structure to a single-page PDF with walls, entry marker, and exit marker, auto-scaling cell size so any grid fits within the printable area of the selected page size.
- `cli-menu`: Present a text menu mapping difficulty choices to concrete maze parameters, offer an "editar dificultades" flow, auto-open the generated PDF, and drive the generate→render pipeline while handling invalid input gracefully.
- `preset-configuration`: Load, edit, validate, and persist the difficulty presets (name → grid size) in a JSON config file on the user's machine, falling back to built-in defaults when the file is absent or corrupt.

### Modified Capabilities

<!-- None — this is a greenfield project. -->

## Impact

- **Code**: New Python package (tentatively `maze_pdf/`) with modules for generation, rendering, CLI, and config.
- **Dependencies**: Adds one third-party PDF library (candidate: `reportlab`, decision deferred to `design.md`). Standard library only for the maze algorithm, CLI, config persistence (`json`), and auto-open (`os.startfile` / `subprocess`).
- **Packaging**: New `pyproject.toml` (or `requirements.txt`) + minimal `README`/`leame.md` update.
- **APIs**: None — no network or external API surface.
- **Runtime**: Local CLI only; **one persistent file** (`~/.laberinto.json`) holding user-edited difficulty presets; generated PDFs written to the working directory.
