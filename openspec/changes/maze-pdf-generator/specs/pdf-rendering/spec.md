## ADDED Requirements

### Requirement: Render one or more mazes to a multi-page PDF

The system SHALL render a sequence of `Maze` data structures to a PDF file at a caller-specified path, producing **one page per maze in order**, with all walls drawn as black lines on a white background. The sequence MUST contain at least one maze.

#### Scenario: Single maze produces a one-page PDF
- **WHEN** `render_to_pdf([maze], path="out.pdf")` is called with a single 15×15 maze
- **THEN** a file `out.pdf` exists on disk
- **AND** the file's first bytes are the PDF magic `%PDF-`
- **AND** the file contains exactly one page

#### Scenario: Multiple mazes produce one page each
- **WHEN** `render_to_pdf([m1, m2, m3], path="out.pdf")` is called with three mazes
- **THEN** the PDF contains exactly three pages
- **AND** each page shows a different maze in the given order

#### Scenario: Empty sequence rejected
- **WHEN** `render_to_pdf([], path="out.pdf")` is called with no mazes
- **THEN** the renderer raises `ValueError`
- **AND** no file is created

#### Scenario: Entry and exit are visually open
- **WHEN** a maze with entry (top-left, north open) and exit (bottom-right, south open) is rendered
- **THEN** the rendered page has a visible gap in the outer border at the entry cell's top edge
- **AND** a visible gap at the exit cell's bottom edge

### Requirement: Always fit one page regardless of grid size

The renderer SHALL auto-scale cell size so the whole maze fits within the printable area of the selected page for ANY grid size N ≥ 2: smaller grids produce larger cells (easier to solve visually), larger grids produce smaller cells (denser, harder). The rendered maze SHALL preserve aspect ratio and MUST leave uniform margins of at least 15 mm on every side.

#### Scenario: Small grid yields large cells
- **WHEN** a 5×5 maze is rendered to an A4 page
- **THEN** the cell pixel size is at least 4× the cell size used for a 40×40 maze on the same page

#### Scenario: Large grid still fits one page
- **WHEN** a 60×60 maze is rendered to an A4 page
- **THEN** no wall line extends beyond the 15 mm margin on any side
- **AND** the output has exactly one page

#### Scenario: Page never overflows
- **WHEN** any maze with `width >= 2, height >= 2` is rendered
- **THEN** the resulting PDF has exactly one page
- **AND** every wall line lies within the printable area (page size minus 15 mm margins on each side)

### Requirement: Selectable page size

The renderer SHALL accept a `page_size` argument with values `"a4"` (default) and `"letter"`, producing the corresponding PDF page dimensions.

#### Scenario: Default A4 page
- **WHEN** a maze is rendered without a page-size argument
- **THEN** the output PDF has an A4 page (210 × 297 mm)

#### Scenario: Letter page override
- **WHEN** `render_to_pdf(maze, path, page_size="letter")` is called
- **THEN** the output PDF has a Letter page (8.5 × 11 in)

#### Scenario: Invalid page size rejected
- **WHEN** `render_to_pdf(maze, path, page_size="a3")` is called
- **THEN** the renderer raises `ValueError` without creating the output file

### Requirement: Wall line weight scales with grid size

The renderer SHALL choose a wall line weight that remains visible when printed. Minimum tiers:
- N ≤ 25 → line weight ≥ 0.75 pt
- 25 < N ≤ 40 → line weight ≥ 0.5 pt
- 40 < N ≤ 60 → line weight ≥ 0.4 pt
- N > 60 → best-effort at 0.3 pt; the renderer still succeeds but a warning SHALL be emitted.

#### Scenario: Complex maze lines remain printable
- **WHEN** a 40×40 maze is rendered to an A4 page
- **THEN** the line weight used is >= 0.5 pt

#### Scenario: Very large maze emits warning
- **WHEN** a 70×70 maze is rendered
- **THEN** the PDF is produced
- **AND** a warning is emitted mentioning that lines may print too thin
