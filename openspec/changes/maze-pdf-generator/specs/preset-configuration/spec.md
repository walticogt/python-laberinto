## ADDED Requirements

### Requirement: Built-in default presets

The system SHALL define a hard-coded mapping of default presets: `simple=15`, `medium=25`, `complex=40` (each representing an N×N square grid). These defaults SHALL be used whenever no user-edited config is available.

#### Scenario: Defaults available with no config file
- **WHEN** the config file path does not exist on disk
- **THEN** `load_presets()` returns a mapping with exactly three entries: `simple=15`, `medium=25`, `complex=40`

### Requirement: Load presets from JSON config

The system SHALL load presets from a JSON file at `~/.laberinto.json` (or a path supplied via `--config`) using the schema `{"presets": {"simple": <int>, "medium": <int>, "complex": <int>}}`.

#### Scenario: Valid config file overrides defaults
- **WHEN** `~/.laberinto.json` contains `{"presets": {"simple": 10, "medium": 20, "complex": 30}}`
- **AND** `load_presets()` is called
- **THEN** the returned mapping is `{"simple": 10, "medium": 20, "complex": 30}`

#### Scenario: Malformed config falls back to defaults
- **WHEN** the config file exists but is not valid JSON
- **THEN** `load_presets()` returns the built-in defaults
- **AND** a single warning line is printed to stderr naming the file and the parse error
- **AND** no exception propagates out of `load_presets()`

#### Scenario: Partial config file
- **WHEN** the config file contains only a subset of keys (e.g. only `simple`)
- **THEN** missing keys are filled from the built-in defaults, and the merged mapping is returned

### Requirement: Save presets to JSON config

The system SHALL provide a `save_presets(presets, path=None)` function that writes the mapping to the JSON config, creating the file if absent and overwriting atomically (write to a temp file, then rename).

#### Scenario: Save creates a readable config
- **WHEN** `save_presets({"simple": 12, "medium": 22, "complex": 33})` is called with a temp path
- **THEN** the file exists at that path
- **AND** `load_presets(path=<same>)` returns `{"simple": 12, "medium": 22, "complex": 33}`

#### Scenario: Save does not corrupt config on interrupted write
- **WHEN** `save_presets` is interrupted after writing the temp file but before renaming
- **THEN** the original config file (if any) remains intact and parseable

### Requirement: Validate preset values on save

The system SHALL reject saves where any preset value is not an integer `N` with `N >= 2`, raising a `ValueError` that names the offending key and value.

#### Scenario: Reject too-small preset
- **WHEN** `save_presets({"simple": 1, "medium": 20, "complex": 40})` is called
- **THEN** a `ValueError` is raised mentioning `simple` and the value `1`
- **AND** the config file is not modified

#### Scenario: Reject non-integer preset
- **WHEN** `save_presets({"simple": "fifteen", "medium": 20, "complex": 40})` is called
- **THEN** a `ValueError` is raised mentioning `simple`

#### Scenario: Warn but accept large preset
- **WHEN** `save_presets({"simple": 15, "medium": 25, "complex": 80})` is called
- **THEN** the save succeeds
- **AND** a warning is printed that preset `complex` (N=80) may produce lines too thin to print
