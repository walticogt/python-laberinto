## ADDED Requirements

### Requirement: Interactive difficulty menu

When invoked without arguments, the CLI SHALL display a Spanish-language menu with the current preset sizes and SHALL read a single line of input to select one. The menu SHALL include the three difficulty options, an "Editar dificultades" option, and a "Salir" option.

#### Scenario: Menu shows current preset values
- **WHEN** the user runs the CLI with presets `simple=15, medium=25, complex=40`
- **THEN** the menu displays lines including `Básico    (15 x 15)`, `Medio     (25 x 25)`, and `Complejo  (40 x 40)`
- **AND** also displays `Editar dificultades` and `Salir` options

#### Scenario: Valid selection generates and saves a PDF
- **WHEN** the user runs the CLI with no arguments and enters `2`
- **THEN** a maze using the current `medium` preset is generated
- **AND** a PDF file is written to the working directory
- **AND** the CLI prints the absolute path of the written file
- **AND** the CLI attempts to open the PDF with the OS default application
- **AND** exits with status 0

#### Scenario: Invalid selection reprompts
- **WHEN** the user enters a value that is not a listed option (e.g. `foo`, `0`, `9`)
- **THEN** the CLI prints a brief error message
- **AND** redisplays the menu
- **AND** does NOT exit until a valid choice is made or the user sends EOF/Ctrl-C

#### Scenario: Salir exits cleanly
- **WHEN** the user picks the `Salir` option
- **THEN** the CLI exits with status 0 without generating a maze

### Requirement: Edit-presets flow

The menu SHALL provide an option that walks the user through editing each preset in order (`simple`, `medium`, `complex`), prompting for a new integer N for each. Blank input SHALL keep the current value. On completion, the new presets SHALL be persisted via the `preset-configuration` capability.

#### Scenario: Editing updates config and is visible on next menu
- **WHEN** the user picks `Editar dificultades`
- **AND** enters `10` for `Básico`, blank for `Medio`, and `50` for `Complejo`
- **THEN** the config file is updated so `simple=10`, `medium` is unchanged, and `complex=50`
- **AND** the CLI returns to the main menu
- **AND** the main menu now displays `Básico (10 x 10)` and `Complejo (50 x 50)`

#### Scenario: Invalid edit input reprompts that preset
- **WHEN** during the edit flow the user enters `abc` or `0` or `-5`
- **THEN** the CLI prints an error naming the allowed range (integer >= 2)
- **AND** reprompts for the same preset without advancing to the next one

### Requirement: Auto-open generated PDF

After a successful generation+render, the CLI SHALL invoke a cross-platform opener that asks the OS to display the PDF in its default application, unless `--no-open` is passed. Opener failures SHALL be non-fatal.

#### Scenario: Successful open on supported platform
- **WHEN** the CLI finishes writing a PDF on Windows/macOS/Linux
- **AND** `--no-open` is not set
- **THEN** the opener is invoked with the absolute PDF path
- **AND** the CLI exits with status 0

#### Scenario: --no-open suppresses auto-open
- **WHEN** the CLI is run with `--no-open`
- **THEN** the PDF is written
- **AND** the opener is NOT invoked
- **AND** the CLI exits with status 0

#### Scenario: Opener failure is non-fatal
- **WHEN** the opener raises an exception or returns False (e.g. no default viewer)
- **THEN** the CLI prints a warning with the PDF's absolute path
- **AND** exits with status 0 because the PDF was successfully produced

### Requirement: Non-interactive flags for scripting

The CLI SHALL accept the flags `--difficulty {simple,medium,complex}`, `--output <path>`, `--seed <int>`, `--pages <int>`, `--no-open`, and `--config <path>` to bypass the interactive menu. `--pages` MUST be an integer in `[1, 10]`; invalid values exit non-zero with a stderr message.

#### Scenario: Scripted invocation with all flags
- **WHEN** the user runs `maze_pdf --difficulty complex --output /tmp/x.pdf --seed 7 --pages 3 --no-open`
- **THEN** no prompt is shown
- **AND** `/tmp/x.pdf` is written containing three complex-preset mazes on three pages
- **AND** no opener is invoked
- **AND** the process exits with status 0

#### Scenario: Invalid difficulty flag
- **WHEN** the user runs `maze_pdf --difficulty impossible`
- **THEN** the CLI prints an error to stderr and exits with a non-zero status

#### Scenario: Invalid pages flag
- **WHEN** the user runs `maze_pdf --difficulty simple --pages 0` or `--pages 11`
- **THEN** the CLI prints an error to stderr and exits with a non-zero status

#### Scenario: Custom config path
- **WHEN** the user runs `maze_pdf --config /tmp/my-presets.json`
- **THEN** presets are loaded from `/tmp/my-presets.json`
- **AND** edits made via the edit flow are written back to that same path

### Requirement: Page-count prompt in interactive menu

After the user selects a difficulty from the main menu, the CLI SHALL prompt for a page count with a default of 1 and a maximum of 10. Blank input SHALL default to 1. Invalid input SHALL reprompt without falling back to the main menu.

#### Scenario: Default of 1 with blank input
- **WHEN** the user selects `Básico` and then presses Enter at the page-count prompt without typing
- **THEN** the generated PDF has exactly one page

#### Scenario: Valid page count N produces N-page PDF
- **WHEN** the user selects `Medio` and enters `4` at the page-count prompt
- **THEN** the generated PDF has exactly four pages
- **AND** each page is a different maze

#### Scenario: Invalid page-count input reprompts
- **WHEN** the user enters `abc`, `0`, `-1`, or `11` at the page-count prompt
- **THEN** the CLI prints an error naming the allowed range (integer 1–10)
- **AND** reprompts for the page count

### Requirement: Multi-page seeding semantics

When `--seed S` is passed together with `--pages N > 1` (or via the interactive prompt), page `i` (0-indexed) SHALL be generated with seed `S + i`. When no seed is passed, each page SHALL use an independent non-deterministic seed.

#### Scenario: Seed + multiple pages is reproducible
- **WHEN** `maze_pdf --difficulty simple --pages 3 --seed 10 --output a.pdf --no-open` is run twice
- **THEN** the two output PDFs have byte-identical maze structures on each of their three pages

### Requirement: Difficulty resolution uses current presets

The CLI SHALL resolve each difficulty name to the grid size from the currently loaded preset configuration (not from hard-coded constants), so edits made via the menu take effect immediately for subsequent generations in the same run.

#### Scenario: Edit then generate uses new size
- **WHEN** the user edits `simple` to `8` and then selects `Básico` from the main menu
- **THEN** the generated maze is 8×8
