# Copilot Scaffolding Prompt — Biobasis Daily Met Merge (Python & R, Minimal Config, UTC)

> **Goal:** Create a dual-language (Python + R) CLI tool per the README/specs below. Minimal config (input_dir, output_dir, date_start, date_end). UTC only, **no timezone conversions**. No notebooks.

**You are GitHub Copilot. Do the following, step by step:**

## 1) Scaffold the repo
- Create folders and files exactly as:
```
biobasis-merge/
  configs/biobasis_merge.yaml
  python/biobasis_merge_py/{__init__.py,main.py,cli.py,io_files.py,parse_header.py,merge_logic.py,metadata.py,plots.py,utils.py}
  python/biobasis_merge_py/tests/{test_cli.py,test_parse_header.py,test_merge_logic.py,test_plots.py}
  R/R/{main.R,cli.R,io_files.R,parse_header.R,merge_logic.R,metadata.R,plots.R,utils.R}
  R/tests/testthat/{test_cli.R,test_parse_header.R,test_merge_logic.R,test_plots.R}
  R/DESCRIPTION
  README.md
  .gitignore
  LICENSE
```
- Copy the **README / Specs** content into `README.md`.
- Put the minimal YAML example into `configs/biobasis_merge.yaml`.

## 2) Python implementation
- `cli.py`: Typer or argparse CLI with `--config`, `--dry-run`, `--overwrite`.
- `utils.py`: parse config (YAML), parse dates (`YYYYMMDD` or ISO), format run range strings, logging setup.
- `io_files.py`: build expected `YYYYMMDD` list; map to `input_dir/Biobasis_MM1_{date}.dat`; existence checks; file reader returning `(df, metadata)` where metadata rows 3–4 become a tidy frame.
- `parse_header.py`: handle 4-line header; use Row 2 as column names; capture Row 3 as units; Row 4 as stat.
- `merge_logic.py`: concat, sort by `TIMESTAMP`, de-dup (keep first), build **naïve UTC** index from start 00:00:00 to end 23:30:00 at 30-min, reindex and fill with `NaN`.
- `metadata.py`: consolidate units/stat across files; prefer first non-NA unit/stat per column.
- `plots.py`: Plotly subplots to HTML (exclude `TIMESTAMP`, `RECORD`); auto grid with max 2 columns; downsample via stride if rows > 200k.
- `main.py`: orchestrate pipeline, write outputs:
  - Parquet + CSV.GZ: `Biobasis_MM1_merged_{date_start}-{date_end}.*`
  - Metadata: `*_metadata.csv`
  - Plots: `*_plots.html`
  - Print summary (files expected/found, rows, missing timestamps, outputs).

## 3) R implementation (mirror Python features)
- `cli.R`: optparse/argparse; same flags.
- `io_files.R`, `parse_header.R`, `merge_logic.R`, `metadata.R`, `plots.R`, `utils.R`: same responsibilities as Python; use `readr` or `data.table`, `dplyr`, `lubridate` (parse times without tz ops), `plotly`, `htmlwidgets`.
- `main.R`: orchestrate; same outputs and filenames.

## 4) Tests & sample data
- Create `tests/data/` with 3 synthetic daily files:
  - Day 1: full 48 records
  - Day 2: missing some half-hours
  - Day 3: file absent (to test missing file handling)
- Write **pytest** and **testthat** tests for:
  - Header parsing (names/units/stat)
  - Date parsing & file discovery
  - Reindex to 30-min grid (row count for a small range)
  - Duplicate handling (keep first)
  - Plot creation (HTML file exists, expected trace count)

## 5) Non-goals & constraints
- Do **not** add timezone conversions; treat timestamps as UTC labels.
- Do **not** use notebooks.
- Keep CLI surfaces identical between Python and R.

## 6) Quality bar / Acceptance
- Running:
  ```bash
  python -m biobasis_merge_py --config configs/biobasis_merge.yaml
  Rscript R/main.R --config configs/biobasis_merge.yaml
  ```
  produces:
  - Merged Parquet + CSV.GZ
  - Metadata CSV
  - Plotly HTML
  - Console summary with missing files/steps
- Tests pass in both Python and R subprojects.

## 7) Iterate
- Generate code module by module. After each step, show the diff or file content you created.
- If any ambiguity is found, resolve using the README/specs above (UTC only, minimal config, 4-row header with names/units/stat).
- When done, provide a **short** run guide and the list of created files.

**End of prompt.**
