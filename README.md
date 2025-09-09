# Biobasis Daily Met Merge Tool

A dual-language (Python + R) CLI tool for merging daily meteorological data files with UTC timestamps and calculating advanced meteorological parameters including WBGT heat stress index.

## Overview

This tool merges multiple daily Biobasis meteorological data files into a single dataset with consistent 30-minute intervals. It handles missing data, creates visualizations, and outputs results in multiple formats. Additionally, it calculates meteorological parameters including saturated vapor pressure, dewpoint temperature, wet-bulb temperature, and the Wet-Bulb Globe Temperature (WBGT) heat stress index using Campbell Scientific formulas.

## Features

- **Dual Implementation**: Identical functionality in both Python and R
- **UTC Timestamps**: No timezone conversions, treats all timestamps as UTC labels
- **Flexible Input**: Supports YYYYMMDD or ISO date formats
- **Multiple Outputs**: CSV, metadata CSV, and interactive HTML plots
- **Data Quality**: Handles missing files, duplicate timestamps, and irregular intervals
- **Meteorological Calculations**: Campbell Scientific WBGT heat stress index and related parameters
- **Testing**: Comprehensive test suites for both implementations

## File Format

Input files follow the pattern `Biobasis_MM1_YYYYMMDD.dat` with a 4-line header:
- Line 1: File identifier/metadata
- Line 2: Column names  
- Line 3: Units for each column
- Line 4: Statistics type for each column

Data follows at 30-minute intervals with `TIMESTAMP` and `RECORD` columns plus meteorological variables.

## Meteorological Calculations

The tool calculates advanced meteorological parameters based on Campbell Scientific formulas, particularly for heat stress monitoring using the Wet-Bulb Globe Temperature (WBGT) index:

### Input Variables Required
- `BGTemp_C_Avg`: Black globe temperature (°C) 
- `AirTC_Avg`: Air temperature (°C)
- `RH_Avg`: Relative humidity (%)
- `P_Air_Avg`: Air pressure (mbar)

### Calculated Parameters
1. **Saturated Vapor Pressure (esat_kPa)**: Using exponential formula
2. **Vapor Pressure (ea_kPa)**: From relative humidity and saturated vapor pressure
3. **Dewpoint Temperature (dewpoint_C)**: Using Teten's equation
4. **Wet-Bulb Temperature (wet_bulb_C)**: Iterative convergence method with 0.01°C tolerance
5. **WBGT (WBGT_C)**: Campbell Scientific formula: **WBGT = 0.2 × Black Globe + 0.7 × Wet-bulb + 0.1 × Air Temperature**

### References
- Campbell Scientific Black Globe Temperature Manual
- Standard meteorological formulas for vapor pressure calculations
- Iterative wet-bulb temperature calculation methods

## Installation

### Python
```bash
cd python
pip install -r requirements.txt
```

### R
```r
# Install required packages
install.packages(c("optparse", "readr", "dplyr", "lubridate", "plotly", "htmlwidgets", "yaml", "arrow"))
```

## Usage

### Python
```bash
python -m biobasis_merge_py --config configs/biobasis_merge.yaml
python -m biobasis_merge_py --config configs/biobasis_merge.yaml --dry-run
python -m biobasis_merge_py --config configs/biobasis_merge.yaml --overwrite
```

### R
```bash
Rscript R/main.R --config configs/biobasis_merge.yaml
Rscript R/main.R --config configs/biobasis_merge.yaml --dry-run
Rscript R/main.R --config configs/biobasis_merge.yaml --overwrite
```

## Configuration

Edit `configs/biobasis_merge.yaml`:

```yaml
input_dir: "data/input"
output_dir: "data/output" 
date_start: "20240101"  # YYYYMMDD or YYYY-MM-DD
date_end: "20240103"
```

## Outputs

For date range 20240101-20240103:
- `Biobasis_MM1_merged_20240101-20240103.csv` (uncompressed CSV with all original + calculated columns)
- `Biobasis_MM1_merged_20240101-20240103_metadata.csv` (column metadata: units, statistics)
- `Biobasis_MM1_merged_20240101-20240103_plots.html` (interactive Plotly visualizations including WBGT)

The main CSV output includes all original meteorological variables plus 5 calculated parameters:
- `esat_kPa`: Saturated vapor pressure (kPa)
- `ea_kPa`: Actual vapor pressure (kPa)
- `dewpoint_C`: Dewpoint temperature (°C) 
- `wet_bulb_C`: Wet-bulb temperature (°C)
- `WBGT_C`: Wet-Bulb Globe Temperature heat stress index (°C)

## Testing

### Python
```bash
cd python
pytest biobasis_merge_py/tests/
```

### R
```r
library(testthat)
setwd("R")
test_dir("tests/testthat")
```

## Data Processing Pipeline

1. **File Discovery**: Find all expected daily files in date range
2. **Header Parsing**: Extract column names, units, and statistics from 4-line headers
3. **Data Loading**: Read CSV data with timestamp parsing
4. **Merging**: Concatenate all daily datasets
5. **Deduplication**: Remove duplicate timestamps (keep first occurrence)
6. **Reindexing**: Create complete 30-minute grid from start 00:00:00 to end 23:30:00
7. **Gap Filling**: Fill missing timestamps with NaN values
8. **Meteorological Calculations**: Calculate WBGT heat stress index and related parameters
9. **Metadata Consolidation**: Merge units and statistics across files
10. **Output Generation**: Write CSV, metadata, and interactive plots

## Architecture

```
configs/                    # Configuration files
python/biobasis_merge_py/   # Python implementation
├── __init__.py
├── main.py                 # Main orchestration
├── cli.py                  # Command-line interface
├── utils.py                # Configuration and utilities
├── io_files.py             # File I/O operations
├── parse_header.py         # Header parsing logic
├── merge_logic.py          # Data merging and reindexing
├── meteorology.py          # Campbell Scientific WBGT calculations
├── metadata.py             # Metadata consolidation
├── plots.py                # Visualization generation
└── tests/                  # Python tests
R/                          # R implementation
├── R/                      # R source files (mirrors Python)
│   ├── meteorology.R       # Campbell Scientific WBGT calculations
├── DESCRIPTION             # R package description
└── tests/testthat/         # R tests
tests/data/                 # Synthetic test data
```

## Design Principles

- **UTC Only**: No timezone conversions, timestamps treated as UTC labels
- **Minimal Configuration**: Only essential parameters in config
- **Identical Interfaces**: Python and R CLIs have same flags and behavior
- **Robust Error Handling**: Graceful handling of missing files and malformed data
- **Comprehensive Testing**: Both unit tests and integration tests
- **Clear Reporting**: Detailed console output with processing summary
- Read daily half-hourly meteorological files named `Biobasis_MM1_YYYYMMDD.dat`
- Merge over a **date range**
- Enforce a **continuous 30-minute** time grid (insert missing steps as `NaN`/`NA`)
- Export **merged data** (CSV+Parquet), **metadata** (units/stats), and **interactive Plotly HTML subplots**

> **No notebooks.** Pure scripts + CLI.  
> **Minimal config**: only `input_dir`, `output_dir`, `date_start`, `date_end`.  
> **Time handling**: treat timestamps as **UTC** with **no timezone conversions**.

---

## Minimal Config (shared YAML)
```yaml
# configs/biobasis_merge.yaml
input_dir: "O:/Tech_ICOS/Data/GL-ZaF/1.raw/MM1"
output_dir: "O:/Tech_ICOS/Data/GL-ZaF/2.processed/biobasis_merge"
date_start: "20250101"  # inclusive; accepts YYYYMMDD or YYYY-MM-DD
date_end:   "20250901"  # inclusive; accepts YYYYMMDD or YYYY-MM-DD
```

---

## File Format (canonical)
- **Filename:** `Biobasis_MM1_YYYYMMDD.dat` (daily)
- **Delimiter/quotes:** CSV with `,` and `"`
- **Header rows:** exactly **4**
  1) metadata (TOA5 line)  
  2) **column names** (use these)  
  3) **units** (kept as metadata)  
  4) **qualifiers/stat** (e.g., Avg/Max; kept as metadata)
- **TIMESTAMP**: `"YYYY-MM-DD hh:mm:ss"` (quoted), 30-min cadence

---

## Behavior & Defaults (hard-coded)
- **Parsing:** UTF-8, `,`, `"`, header row 2 (1-based). Non-time columns coerced numeric.
- **Merge:** concat rows, sort by `TIMESTAMP`, de-dup (keep first; log).
- **Timeline:** full 30-min grid from `date_start 00:00:00` to `date_end 23:30:00` (UTC, **no tz ops**). Insert missing rows; fill others with `NaN`/`NA`.
- **Outputs:**
  - `Biobasis_MM1_merged_{date_start}-{date_end}.csv` (uncompressed with meteorological calculations)
  - `Biobasis_MM1_merged_metadata.csv` (units + stat)
  - `Biobasis_MM1_merged_{date_start}-{date_end}_plots.html` (Plotly with WBGT visualizations)
- **Logging:** INFO to console (and file if implemented). Summary report at end.

---

## Project Structure
```
biobasis-merge/
  configs/
    biobasis_merge.yaml
  python/
    biobasis_merge_py/
      __init__.py
      main.py           # entrypoint wires CLI -> pipeline
      cli.py            # Typer/argparse CLI, --config/--dry-run/--overwrite
      io_files.py       # date->filenames, existence, read single file
      parse_header.py   # row2 names, row3 units, row4 stat
      merge_logic.py    # concat, sort, de-dup, 30-min reindex
      metadata.py       # assemble units/stat table
      plots.py          # Plotly subplots -> HTML
      utils.py          # date parsing (YYYYMMDD/ISO), logging helpers
      tests/            # pytest: unit + integration
      pyproject.toml
  R/
    R/
      main.R
      cli.R             # optparse/argparse; mirrors Python CLI
      io_files.R
      parse_header.R
      merge_logic.R
      metadata.R
      plots.R
      utils.R
      tests/            # testthat
    DESCRIPTION
  .gitignore
  README.md
  LICENSE
```
---

## Install (suggested)
**Python**
```bash
# inside repo root
python -m venv .venv && . .venv/Scripts/activate  # or source .venv/bin/activate (mac/linux)
pip install -e ./python/biobasis_merge_py
# or: pip install pandas pyarrow plotly pyyaml typer pytest
```

**R**
```r
# inside repo root
# install.packages(c("yaml","readr","data.table","dplyr","lubridate","plotly","htmlwidgets","optparse","testthat"))
```

---

## Usage
**Python**
```bash
python -m biobasis_merge_py --config configs/biobasis_merge.yaml
# options:
#   --dry-run      # scan/report only, no outputs
#   --overwrite    # overwrite existing outputs
```

**R**
```bash
Rscript R/main.R --config configs/biobasis_merge.yaml
# options mirror Python: --dry-run, --overwrite
```

CLI prints:
- Files detected vs expected
- Rows merged, duplicates encountered
- Missing timestamps inserted
- Output paths

---

## Outputs
- Merged: Uncompressed CSV with meteorological calculations
- Metadata: CSV (columns: `name`, `units`, `stat`)
- Plots: HTML with one time-series panel per numeric variable (exclude `TIMESTAMP`, `RECORD`), includes WBGT heat stress index

---

## Testing (must have)
- **Sample data**: 3 days in `tests/data/`  
  - Day A: perfect 48 records  
  - Day B: missing some intervals  
  - Day C: file missing entirely
- **Unit tests**:
  - Header parsing (names/units/stat)
  - Date parsing (`YYYYMMDD` and ISO)
  - Reindex to 30-min grid (row count check)
  - Duplicate handling (keep first)
  - Plot file created with expected traces
- **Integration test**: run CLI on sample config; verify outputs and summary.

---

## Acceptance Criteria
- Reads all existing files in range; logs missing day files.
- Produces **continuous** 30-min series (no tz shifts) from start to end inclusive.
- Inserts missing timestamps, fills non-time variables with `NaN`/`NA`.
- Exports merged Parquet + CSV.GZ, metadata CSV, and Plotly HTML.
- CLI `--dry-run` prints intended actions; `--overwrite` replaces outputs.
- Python and R outputs are **column-compatible** (same headers) given same inputs.

---

## Known Constraints
- Assumes exactly 4 header rows with `TIMESTAMP` present on Row 2.
- Treats all times as UTC **labels**; **no DST/tz conversions**.
- If columns differ across days, union by column name; missing columns become `NaN`/`NA`.

---

## .gitignore (suggested)
```
# Python
.venv/
__pycache__/
*.pyc
.python-version

# R
.Rproj.user/
.Rhistory
.RData
.Ruserdata

# Outputs & logs
*.log
*.html
*.csv
*.csv.gz
*.parquet

# OS
.DS_Store
Thumbs.db
```
