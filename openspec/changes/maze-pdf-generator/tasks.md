## 1. Project setup

- [x] 1.1 Create `pyproject.toml` with project metadata, Python >=3.11 requirement, and a `[project.scripts]` entry `laberinto = "maze_pdf.cli:main"`
- [x] 1.2 Declare `reportlab` as the sole runtime dependency; add `pytest` as a dev dependency
- [x] 1.3 Create the `maze_pdf/` package directory with empty `__init__.py` and a `__main__.py` that calls `cli.main()`
- [x] 1.4 Create `tests/` directory with empty `__init__.py`
- [x] 1.5 Add a short `README.md` (or update `leame.md`) covering install (`pip install -e .`), usage (`laberinto` / `laberinto --difficulty medium`), and where the config file lives (`~/.laberinto.json`)

## 2. Preset configuration module (`preset-configuration` spec)

- [x] 2.1 Create `maze_pdf/presets.py` with a `DEFAULT_PRESETS: dict[str, int]` = `{"simple": 15, "medium": 25, "complex": 40}`
- [x] 2.2 Add `DEFAULT_CONFIG_PATH = Path.home() / ".laberinto.json"`
- [x] 2.3 Implement `load_presets(path: Path | None = None) -> dict[str, int]` — reads JSON, merges with defaults for missing keys, falls back silently on missing file, prints one-line stderr warning on malformed JSON
- [x] 2.4 Implement `save_presets(presets: dict[str, int], path: Path | None = None) -> None` — validates (int, N>=2), rejects invalid values with `ValueError` naming the key, writes to `<path>.tmp` then renames for atomic update
- [x] 2.5 Emit a stderr warning from `save_presets` when any preset N > 60 (print legibility risk per design D3)
- [x] 2.6 Add `resolve(presets, name) -> int` helper that raises `ValueError` with a friendly message for unknown names
- [x] 2.7 Add `DISPLAY_LABELS: dict[str, str]` = `{"simple": "Básico", "medium": "Medio", "complex": "Complejo"}` for the menu

## 3. Maze generator (`maze-generation` spec)

- [x] 3.1 Define `Cell` dataclass with `north, south, east, west: bool` wall flags (all True by default)
- [x] 3.2 Define `Maze` dataclass holding `width`, `height`, `cells: list[list[Cell]]`, plus `entry: tuple[int,int]` and `exit: tuple[int,int]`
- [x] 3.3 Implement `generate(width, height, seed=None) -> Maze` using iterative randomized DFS (explicit stack, not recursion)
- [x] 3.4 Validate inputs: raise `ValueError` for `width < 2` or `height < 2`, naming the offending dimension
- [x] 3.5 When `seed is None`, use `random.SystemRandom()`; otherwise use `random.Random(seed)` for deterministic output
- [x] 3.6 After generation, open the north wall of cell (0,0) and the south wall of cell (width-1, height-1); set `entry` / `exit` accordingly

## 4. PDF renderer (`pdf-rendering` spec)

- [x] 4.1 Create `maze_pdf/renderer.py` with `render_to_pdf(maze: Maze, path: str | Path, page_size: str = "a4") -> None`
- [x] 4.2 Lazy-import `reportlab` inside the function (keeps `--help` fast per design risk section)
- [x] 4.3 Validate `page_size` against `{"a4", "letter"}`; raise `ValueError` for anything else, *before* creating any file
- [x] 4.4 Compute cell pixel size so the maze fits within page minus 15 mm margins on all sides, preserving aspect ratio — formula must work for any N from 2 to well beyond 60
- [x] 4.5 Compute line weight by tier: N≤25 → 0.75 pt; 25<N≤40 → 0.5 pt; 40<N≤60 → 0.4 pt; N>60 → 0.3 pt with stderr warning
- [x] 4.6 Draw each cell's walls as line segments; skip walls flagged `False` (including entry/exit gaps)

## 5. Opener module (cross-platform auto-open)

- [x] 5.1 Create `maze_pdf/opener.py` with `open_file(path: Path) -> bool`
- [x] 5.2 Branch on `sys.platform`: `"win32"` → `os.startfile`; `"darwin"` → `subprocess.Popen(["open", ...])`; otherwise → `subprocess.Popen(["xdg-open", ...])`
- [x] 5.3 Wrap the call in `try/except`; return `True` on success, `False` (and print a single stderr warning) on any exception or unknown platform

## 6. CLI (`cli-menu` spec)

- [x] 6.1 Create `maze_pdf/cli.py` with `main(argv: list[str] | None = None) -> int`
- [x] 6.2 Parse flags with `argparse`: `--difficulty {simple,medium,complex}`, `--output PATH`, `--seed INT`, `--no-open`, `--config PATH`
- [x] 6.3 Load presets at startup via `presets.load_presets(args.config)`
- [x] 6.4 If no `--difficulty` flag: enter interactive menu loop showing `Básico (N x N)`, `Medio (N x N)`, `Complejo (N x N)`, `Editar dificultades`, `Salir` with current N values from loaded presets
- [x] 6.5 Implement the "Editar dificultades" flow: prompt for each preset (`simple`, `medium`, `complex`) in order, accept blank to keep current, reject non-integer or N<2 and reprompt the same preset; on completion call `presets.save_presets()` and return to main menu
- [x] 6.6 Map a difficulty selection → N via `presets.resolve()`, call `generator.generate(N, N, seed=args.seed)`, then `renderer.render_to_pdf()`
- [x] 6.7 Default `--output` to `laberinto_<difficulty>.pdf` in CWD when not specified
- [x] 6.8 After write, if not `--no-open`, call `opener.open_file(abs_path)`; print the absolute path regardless of opener result
- [x] 6.9 Handle `KeyboardInterrupt` / EOF during any prompt: print blank line, exit 130
- [x] 6.10 On unexpected errors, print to stderr and return non-zero; on success, return 0 (including when opener fails)

## 7. Tests

- [x] 7.1 `tests/test_generator.py`: perfect-maze properties (`N*N-1` passages, graph connected via BFS, no cycles)
- [x] 7.2 `tests/test_generator.py`: same seed → byte-identical `Maze.cells`; different seeds → differ
- [x] 7.3 `tests/test_generator.py`: `ValueError` for `width=1` and `height=0`
- [x] 7.4 `tests/test_presets.py`: defaults returned when config file missing
- [x] 7.5 `tests/test_presets.py`: malformed JSON → defaults + stderr warning, no exception
- [x] 7.6 `tests/test_presets.py`: round-trip save → load returns identical mapping
- [x] 7.7 `tests/test_presets.py`: `ValueError` for N=1, non-integer, or missing required key on save
- [x] 7.8 `tests/test_renderer.py`: rendered file starts with `%PDF-` and has >0 bytes
- [x] 7.9 `tests/test_renderer.py`: rendering a 60×60 maze succeeds and produces one page
- [x] 7.10 `tests/test_renderer.py`: rendering a 5×5 maze yields larger cell pixel size than a 40×40 maze (sanity check on auto-scaling)
- [x] 7.11 `tests/test_renderer.py`: invalid `page_size` raises `ValueError` without creating a file
- [x] 7.12 `tests/test_cli.py`: `--difficulty simple --output <tmp>.pdf --seed 1 --no-open` writes a valid PDF, exits 0, opener not called
- [x] 7.13 `tests/test_cli.py`: `--difficulty impossible` exits non-zero and writes to stderr
- [x] 7.14 `tests/test_cli.py`: monkeypatch `opener.open_file` to raise; CLI still exits 0 and prints the path
- [x] 7.15 `tests/test_cli.py`: edit flow via stdin input updates the config file written to a temp `--config` path (blank entries preserve previous values)

## 8. Manual verification

- [ ] 8.1 Run `laberinto` with no args, pick each of `Básico` / `Medio` / `Complejo`, confirm: PDF auto-opens, maze fills the page, walls crisp, entry/exit gaps visible
- [ ] 8.2 Use `Editar dificultades` to set `simple=8` and `complex=55`; verify `~/.laberinto.json` contains the new values after exit
- [ ] 8.3 Restart the CLI; confirm menu shows the edited sizes (persistence works across runs)
- [ ] 8.4 Print the `Complejo` PDF on actual paper and solve it — catches "looks fine on screen, too faint to print" bugs
- [ ] 8.5 On Windows cmd/PowerShell, confirm Spanish menu text displays correctly (no mojibake on `Básico`, `Complejo`)
- [ ] 8.6 Run with `--no-open` and confirm no viewer launches; PDF path is still printed

## 9. Multi-page support

- [x] 9.1 Change `render_to_pdf` signature from `(maze, path, ...)` to `(mazes: Sequence[Maze], path, ...)`; raise `ValueError` on empty sequence; emit one page per maze via `c.showPage()` between them
- [x] 9.2 Update all existing callers of `render_to_pdf` in `cli.py` to wrap their single maze in a list
- [x] 9.3 Update existing renderer tests to pass `[maze]` instead of `maze`
- [x] 9.4 Add `--pages N` flag to the CLI argparse (`type=int`); validate `1 <= N <= 10` after parsing and exit non-zero with stderr message on invalid
- [x] 9.5 Add `_prompt_page_count(default=1, maximum=10)` helper in `cli.py`: reprompts on non-integer / out-of-range; blank input returns 1
- [x] 9.6 Wire the page-count prompt into the interactive flow: after difficulty selection but before generation
- [x] 9.7 Implement `_build_mazes(n: int, pages: int, seed: int | None) -> list[Maze]`: when seed given, use `seed + i` per page; when not, generate each maze with a fresh non-deterministic seed
- [x] 9.8 Update `_default_output_path` to include page count when > 1 (e.g. `laberinto_simple_3p.pdf`), to avoid confusing overwrite behavior when user runs several times with different page counts
- [x] 9.9 `tests/test_renderer.py`: rendering a list of 3 mazes produces a PDF with exactly 3 pages (count `/Type /Page` occurrences or parse with `pypdf` if available — else check `showPage` produced multi-page stream)
- [x] 9.10 `tests/test_renderer.py`: empty list raises `ValueError` without creating a file
- [x] 9.11 `tests/test_cli.py`: `--difficulty simple --pages 4 --seed 1 --no-open --output <tmp>.pdf` exits 0 and writes a 4-page PDF
- [x] 9.12 `tests/test_cli.py`: `--pages 0` and `--pages 11` both exit non-zero with stderr
- [x] 9.13 `tests/test_cli.py`: same `(difficulty, pages, seed)` produces byte-identical PDFs across two runs (reproducibility)
- [x] 9.14 `tests/test_cli.py`: interactive flow — monkeypatch `_prompt` to feed `"1"` (difficulty) then `"3"` (pages) then `"5"` (exit nothing generated since difficulty already selected path); assert generated PDF has 3 pages

## 10. Packaging and documentation

- [x] 10.1 Add `pyinstaller>=6` as a `[project.optional-dependencies.build]` extra in `pyproject.toml`
- [x] 10.2 Create `build.ps1` that wraps `pyinstaller --onefile --name laberinto --collect-all reportlab --console maze_pdf/__main__.py` with cleanup of prior `build/` and `dist/`
- [x] 10.3 Expand `leame.md` with: install/usage (kept), config persistence (kept), **`.exe` build instructions**, architecture overview, **Mermaid diagrams** (module dependencies, run flow, DFS algorithm), deep explanation of randomized DFS (why, pseudocode, step-by-step trace of a 3×3 generation), PDF rendering internals (auto-fit math, line weight tiers, no-double-draw strategy), dev/tests section, project layout
- [x] 10.4 Validate build: `pyinstaller` produces `dist/laberinto.exe` (~22 MB), `--help` shows correct Spanish accents, end-to-end `--difficulty simple --pages 2 --seed 1` produces a 2-page PDF
- [x] 10.5 Add `.gitignore` covering `__pycache__/`, `.venv/`, `build/`, `dist/`, `*.spec`, and generated `laberinto_*.pdf`

## 11. Interactive visualizer

- [x] 11.1 Create `docs/maze-visualizer.html` — single-file standalone HTML+CSS+JS visualizer with: seedable PRNG (mulberry32), canvas render, Step/Play/Pause/Finish/Reset controls, live panel showing iteration/stack-depth/current-cell/visited-count/last-action, iteration log, legend, collapsible algorithm source view. Must open with double-click (no server needed) and be deployable as-is to GitHub Pages / Netlify / Vercel
- [x] 11.2 Document in `leame.md` under "Ejecutar el algoritmo paso a paso" section: three ways to open it (local double-click, GitHub Pages, static-host drag-and-drop), honest note about why `<iframe>` embedding doesn't render on GitHub-flavored markdown, list of what the visualizer shows
- [~] 11.3 (abandoned) PSeInt/`docs/laberinto.psc` variant — psintplus.lat's strict parser rejected successive attempts (2D arrays, 1D arrays with Dimension, Dimension after Definir). Kept the `.psc` file but unlinked from README; not worth chasing further compatibility quirks. User can delete `docs/laberinto.psc` if desired
- [x] 11.4 Enhance `docs/maze-visualizer.html`: 3-column layout (canvas | 7-step algorithm panel | estado/legend/log), default grid 5×5, step-by-step highlighting of the currently-executing algorithm phase (step 2 = look at neighbors, 3-4 = pick+advance, 6 = backtrack/pop, 7 = stack empty → open entry/exit), clicking a step advances one iteration

## 12. Windows `.bat` launcher (alternative to `.exe`)

- [x] 12.1 Create `laberinto.bat` at project root: activates `.venv\Scripts\python.exe`, calls `-m maze_pdf` with preselected flags via an echo/choice menu. Covers: 3 quick difficulties (simple/medium/complex), full interactive CLI, custom (difficulty + pages), custom with seed
- [x] 12.2 Fail gracefully if `.venv\Scripts\python.exe` missing — print install instructions and exit 1
- [x] 12.3 Document in `leame.md` under new "Lanzador .bat (sin compilar)" section, with comparison table `.bat` vs `.exe` covering size, portability, rebuild cost

## 13. Tier 1-3 polish round (LICENSE, CI, solver, metadata, algorithms, interactive solver)

- [x] 13.1 (Tier 1.1) Add `LICENSE` file with MIT text matching the README claim
- [x] 13.2 (Tier 1.2) Delete `docs/laberinto.psc` (abandoned PSeInt artifact)
- [x] 13.3 (Tier 1.3) Add `.github/workflows/test.yml` running `pytest` on push/PR for Python 3.11/3.12/3.13 on Ubuntu + Windows
- [x] 13.4 (Tier 1.4) Add `solve(maze)` BFS solver in `generator.py`. Add `--show-solution` CLI flag. Renderer draws the solution as a thick red polyline through cell centers, extending into the entry/exit gaps. Tests cover path correctness (only uses passages, ends at exit, length >= 2N-1)
- [x] 13.5 (Tier 2.1) Embed PDF metadata (title, author, subject, keywords, creator) via reportlab `setTitle`/`setAuthor`/`setSubject`/`setKeywords`/`setCreator`. Title built from difficulty + dimensions
- [x] 13.6 (Tier 2.2) Add per-page header (e.g. "Laberinto 3/10 · Medio · 25x25 · seed 42") rendered in Helvetica 9pt at top-left margin. New `PageInfo` dataclass passed via `page_infos=` param. Reduces usable height by 8mm to make room
- [x] 13.7 (Tier 2.3) Update `build.ps1` to detect optional `docs/laberinto.ico` and pass it to `pyinstaller --icon` when present. Falls back to default icon with a console message if absent
- [x] 13.8 (Tier 2.4) Add commented-out `![demo](docs/demo.gif)` near top of `leame.md` with HTML-comment instructions for capturing the GIF (ScreenToGif/LICEcap, ~5-8 seconds, sub <2 MB)
- [x] 13.9 (Tier 3.1) Add `--width W --height H` CLI flags as override of `--difficulty`. Both must be present together; one alone is `ValueError`. Default file label becomes `WxH` when no preset name available
- [x] 13.10 (Tier 3.2) Add `generate_prim()` (randomized Prim's algorithm) in `generator.py`. Add `generate_with(algorithm, ...)` dispatcher. Add `--algorithm {dfs,prim}` CLI flag (default dfs). Tests verify Prim produces perfect mazes, is deterministic with seed, and produces different mazes than DFS for same seed
- [x] 13.11 (Tier 3.3) Add interactive "modo resolver" to `docs/maze-visualizer.html`: 3 new buttons (Modo resolver, Ver solución, Limpiar intento) enabled only after maze generation finishes. Click + drag on canvas marks cells; only allows moves between adjacent passage-connected cells; rejects wall crossings with a log warning. Detects "win" when path reaches exit. Includes BFS solution overlay in red dashed lines
- [x] 13.12 Test suite expanded from 41 to 60 passing tests covering: rectangular mazes, Prim algorithm, BFS solver path properties, dispatcher, custom dims CLI, show-solution flag, prim flag, PDF size with/without solution, PDF size with/without header, page_infos length validation
