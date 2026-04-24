## Context

Greenfield Python project. Only prior art is an empty `leame.md` and this `openspec/` tree. The owner's goal (see [proposal.md](proposal.md)) is a CLI that produces printable maze PDFs with simple/medium/complex presets. No existing code or team conventions constrain the design.

Stakeholders: the owner is the sole developer and also the primary end-user. The downstream users are people who want to print mazes on paper — so PDF fidelity at standard page sizes matters more than on-screen rendering speed.

Target platform: Windows 11 + Python 3.11+ locally; no reason to preclude Linux/macOS since everything chosen is cross-platform.

## Goals / Non-Goals

**Goals:**
- A runnable CLI (`python -m maze_pdf` or a console-script) that prompts for a difficulty and writes a PDF.
- Perfect mazes (exactly one path between any two cells, no loops, no unreachable cells).
- Deterministic seeding: the same `--seed N` yields the same maze, useful for reproducibility and tests.
- Zero configuration beyond the difficulty choice for the happy path.

**Non-Goals:**
- Non-rectangular shapes (circle, hex, themed images). Architecture should *allow* a future shape plugin, but implementing one is out of scope.
- Solving, hinting, or drawing the solution path on the PDF.
- Internationalization of menu text beyond Spanish (owner's language) — the menu will be in Spanish.
- GUI, web UI, mobile, or printing directly to a printer.

## Decisions

### D1. Maze algorithm: Randomized Depth-First Search (iterative)

**Why**: Produces perfect mazes, trivially correct, easy to seed, O(cells) time. Output has long winding corridors which visually reads as "maze-like" for printed puzzles.

**Alternatives considered**:
- *Prim's* and *Kruskal's* — also correct but produce shorter corridors and more branching; aesthetically busier, harder for a human to perceive as a single challenge. Not a fit for the print use case.
- *Wilson's / Aldous–Broder* — uniform spanning trees, theoretically "nicest", but Aldous–Broder is slow on larger grids and Wilson's adds implementation complexity with no end-user-visible gain for this scale.

### D2. Difficulty = editable grid size, auto-fit to one page

Difficulty is a *single knob* (grid size, N, for an N×N square). Presets are user-editable — the values below are the built-in defaults that ship with the tool, not hard-coded constants.

| Level (internal key) | Display label | Default N | Approx. solve time |
|----------------------|---------------|-----------|--------------------|
| `simple`             | Básico        | 15        | ~1 min             |
| `medium`             | Medio         | 25        | ~3 min             |
| `complex`            | Complejo      | 40        | ~8 min             |

The user edits N through a dedicated menu option; the chosen values persist to a JSON config (see D7). The renderer **always fits one page** by computing cell pixel size from the printable area — so smaller N yields larger, easier-to-draw cells, larger N yields smaller, denser cells. Neither the generator nor the renderer has a hard maximum; a soft advisory triggers when N would push line weight below legibility (see D3 / risks).

**Why**: The user asked for three named presets *plus* the ability to rebalance them later. Treating them as editable config (rather than constants) supports that without adding knobs to the menu itself. Internal keys stay in English (for flags / code); display labels are Spanish.

### D3. PDF library: `reportlab`

**Why**: Pure Python, mature, draws vector primitives (lines) directly — which is exactly what a maze is. Free tier (ReportLab Open Source) has MIT-compatible licensing for this use. No external system dependencies (unlike WeasyPrint, which needs GTK/Pango on Windows).

**Alternatives considered**:
- *matplotlib* — works, but it's a heavy dependency optimized for data plots; line rasterization quality for a pure-vector puzzle is worse and the API is awkward for this.
- *fpdf2* — also viable and lighter than reportlab; reasonable fallback if reportlab becomes a problem. Flag as an open question.
- *Direct SVG → browser print* — sidesteps Python PDF libs entirely but requires the user to open a browser and manually export to PDF. Fails the "one command → one file" UX goal.

### D4. Module layout

```
maze_pdf/
├── __init__.py
├── __main__.py          # enables `python -m maze_pdf`
├── cli.py               # menu + argparse; the only stdin/stdout surface
├── generator.py         # Maze class + randomized DFS
├── renderer.py          # Maze -> reportlab canvas -> PDF file
├── presets.py           # DEFAULT_PRESETS + load/save/validate for config
└── opener.py            # cross-platform "open this file" helper
tests/
├── test_generator.py
├── test_renderer.py
├── test_presets.py
└── test_cli.py
```

**Why**: Clean separation along the four capabilities. Each module is small, independently testable. The renderer doesn't know how mazes are built (it takes a data structure). `presets.py` owns all config I/O. `opener.py` isolates the OS-specific auto-open logic so tests can monkeypatch it.

### D5. Maze in-memory representation

A `Maze` dataclass: `width: int`, `height: int`, `cells: list[list[Cell]]`, where `Cell` is a small dataclass with four `bool` wall flags (`north, south, east, west`). Entry defaults to top-left (remove north wall of (0,0)); exit defaults to bottom-right (remove south wall of (w-1, h-1)).

**Why**: Simple, explicit, trivially serializable for debugging. Bitfield optimization is unnecessary at the target grid sizes (40×40 = 1600 cells).

### D6. CLI behavior

- No arguments → interactive menu in Spanish. The menu displays current preset values so the user sees what they're picking:
  ```
  === Generador de Laberintos ===
    1) Básico    (15 x 15)
    2) Medio     (25 x 25)
    3) Complejo  (40 x 40)
    4) Editar dificultades
    5) Salir
  Elige una opción:
  ```
- Option `4` walks through each preset (`Básico`, `Medio`, `Complejo`) prompting for a new N; blank input keeps the current value. On finish, values are validated (N ≥ 2, soft-warn if N > 60 per D3) and written to the config file.
- Flags for scripted use: `--difficulty {simple,medium,complex}`, `--output FILE.pdf`, `--seed N`, `--no-open` (suppress auto-open), `--config PATH` (override config file location).
- After a successful generation+render, the CLI calls `opener.open_file(path)` unless `--no-open` is set. Failures from the opener are non-fatal: print a warning, keep exit code 0 (the PDF was still produced).
- Invalid menu input loops back to the prompt with a friendly error, doesn't crash. `Ctrl-C` / EOF during any prompt exits cleanly with code 130.

### D7. Preset persistence: JSON at `~/.laberinto.json`

Config file lives at `Path.home() / ".laberinto.json"`. Schema:

```json
{
  "presets": {
    "simple":  15,
    "medium":  25,
    "complex": 40
  }
}
```

**Why**:
- **Home directory, not project directory**: the tool is installed globally (`pip install -e .`) and may be run from anywhere. Putting the config in `$HOME` matches user expectations for a personal CLI.
- **JSON over TOML/YAML**: no extra dependency (`json` is stdlib). Format is human-editable if the user wants to skip the menu.
- **Single integer per preset** (not `[width, height]`): current requirement is square grids only. If rectangular mazes land later, migrate to `{"simple": {"w": 15, "h": 15}}` — the loader will handle both shapes.
- **Missing / malformed file**: fall back to hard-coded `DEFAULT_PRESETS` silently; print a one-line warning on malformed JSON but do not crash.

`--config PATH` override enables testing without touching `$HOME`.

### D9. Multi-page output: renderer takes a list of mazes, hard cap at 10

The renderer accepts a `Sequence[Maze]` (not a single `Maze`) and emits one page per element. The CLI accepts `--pages N` with `1 <= N <= 10`; the interactive menu asks for the same after difficulty is chosen (blank = default 1). When `--seed S` is passed alongside `--pages N > 1`, page `i` (0-indexed) is generated with `seed = S + i` — reproducible AND each page is different. When no seed is passed, every page gets a fresh non-deterministic one.

**Why**:
- **Cap at 10**: printing a single PDF with 10 unique mazes is the realistic upper bound for a home user (one sheet per maze = a stack of 10 puzzles). Higher values are better served by running the tool multiple times with different seeds. Hard cap avoids accidental `--pages 10000`.
- **List-of-mazes API, not "page count" argument**: the renderer stays data-driven. If a future feature wants to mix difficulties on one PDF (e.g. "warm-up page + main"), it already supports it for free.
- **Seed + offset scheme**: simplest reproducibility semantics. Alternative (pass a `Random` instance through the call chain) adds plumbing with no visible benefit to the end-user.

**Alternatives considered**:
- `render_to_pdf(maze, path, copies=N)` — simpler signature but couples pagination to the renderer's input shape and makes "different maze per page" awkward. Rejected.
- Generating one PDF per page and merging with a separate tool — adds filesystem churn and a dependency on `pypdf`. Rejected.

### D8. Auto-open: `os.startfile` on Windows, `xdg-open` / `open` elsewhere

`opener.open_file(path)` dispatches by platform:
- **Windows**: `os.startfile(str(path))` — uses the registered default app for `.pdf` (typically Edge / Acrobat). Does not block.
- **macOS**: `subprocess.Popen(["open", str(path)])`.
- **Linux**: `subprocess.Popen(["xdg-open", str(path)])`.
- On any other platform, or if the call raises: return `False`; CLI prints a warning with the path so the user can open it manually.

**Why**: stdlib-only, no `webbrowser` coupling (the user said "navegador por defecto" as a *fallback idea*, but routing PDFs through the actual OS default viewer is friendlier than forcing a browser). Using `os.startfile` rather than spawning `cmd /c start` avoids a console flash on Windows.

**Alternatives considered**:
- `webbrowser.open("file://" + path)` — cross-platform one-liner but opens the browser specifically; on Windows that might not be the user's preferred PDF viewer.
- `click.launch(path)` — same behavior as above but adds a dependency.

## Risks / Trade-offs

- **reportlab dependency size** → Mitigation: it's ~5 MB; acceptable for a CLI tool that users `pip install` once. Keep import lazy so `--help` stays snappy.
- **Windows console encoding for Spanish characters** (`ñ`, accents) → Mitigation: force `sys.stdout.reconfigure(encoding="utf-8")` at CLI entry, or use plain ASCII prompts as a fallback ("Medio" not "Medió").
- **User edits a preset to an extreme N (e.g. 200)** → Mitigation: hard minimum N=2 rejected; soft warning at N>60 ("may print too faint to solve"); render still attempts to fit — the user is trusted to judge their own printer.
- **Recursive DFS could hit Python recursion limit on large grids** → Mitigation: use the *iterative* variant with an explicit stack (this is already the chosen algorithm per D1).
- **Single exit shape (rectangular) limits future themed mazes** → Mitigation: accepted; the `Maze` dataclass is shape-agnostic enough that a future `CircularMaze` could share the same renderer contract.
- **Auto-open fails silently or opens the wrong app** → Mitigation: `opener` prints the resolved path before calling out to the OS, so even if the viewer fails to launch the user sees where the PDF is. `--no-open` available for CI/scripted runs.
- **Corrupt config file blocks startup** → Mitigation: loader catches `json.JSONDecodeError` and falls back to defaults with a single warning line; user can fix the file via the menu's edit flow or delete it to reset.

## Open Questions

1. **reportlab vs fpdf2**: Go with reportlab as the default; revisit only if licensing or install friction surfaces during implementation.
2. **Page size**: default to Letter (US) or A4 (most of Latin America)? Proposed default: **A4**, with `--page letter` override. Confirm during implementation.
3. **Console script name**: `maze-pdf`? `laberinto`? Owner to decide; defaulting to `laberinto` given the repo name and Spanish UI.
