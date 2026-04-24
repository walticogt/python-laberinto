## ADDED Requirements

### Requirement: Generate a perfect rectangular maze

The system SHALL generate a perfect maze — a rectangular grid of cells where exactly one path exists between any two cells (no loops, no unreachable cells) — for any requested `width >= 2` and `height >= 2`.

#### Scenario: Valid size produces a perfect maze
- **WHEN** the generator is called with `width=15, height=15`
- **THEN** the returned maze has 225 cells
- **AND** every cell is reachable from every other cell (graph is connected)
- **AND** the number of passages is exactly `width * height - 1` (tree structure; no cycles)

#### Scenario: Minimum size
- **WHEN** the generator is called with `width=2, height=2`
- **THEN** the returned maze has 4 cells and 3 passages

#### Scenario: Invalid size
- **WHEN** the generator is called with `width=1` or `height=0`
- **THEN** the system SHALL raise a `ValueError` with a message naming the invalid dimension

### Requirement: Deterministic generation via seed

The system SHALL accept an optional integer seed and MUST produce byte-identical maze output for the same `(width, height, seed)` triple across runs.

#### Scenario: Same seed, same maze
- **WHEN** `generate(width=20, height=20, seed=42)` is called twice
- **THEN** both returned mazes have identical wall configurations for every cell

#### Scenario: Different seeds, different mazes
- **WHEN** `generate(width=20, height=20, seed=1)` and `generate(width=20, height=20, seed=2)` are called
- **THEN** their wall configurations differ in at least one cell

#### Scenario: No seed provided
- **WHEN** `generate(width=20, height=20)` is called without a seed
- **THEN** the system SHALL use a non-deterministic source (e.g. `os.urandom` / `random.SystemRandom`) so repeated calls produce different mazes

### Requirement: Entry and exit markers

The maze data structure SHALL designate exactly one entry cell and one exit cell, with the boundary wall on that side of each cell removed so the entry/exit are visually open on the perimeter.

#### Scenario: Default entry/exit placement
- **WHEN** a maze is generated without explicit entry/exit arguments
- **THEN** the entry is the top-left cell with its north wall removed
- **AND** the exit is the bottom-right cell with its south wall removed
