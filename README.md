# Biobasis Daily Met Merge Tool

A dual-language (Python + R) CLI tool for merging daily meteorological data files with advanced WBGT heat stress calculations based on Campbell Scientific formulas.

## Overview

This tool merges multiple daily Biobasis meteorological data files into a single dataset with consistent 30-minute intervals. It calculates the Wet-Bulb Globe Temperature (WBGT) heat stress index and related meteorological parameters using Campbell Scientific formulas.

## Key Features

- **WBGT Heat Stress Index**: Campbell Scientific formula implementation
- **Dual Implementation**: Identical functionality in Python and R
- **Robust Data Processing**: Handles missing files, duplicate timestamps, and irregular intervals
- **Interactive Visualizations**: Plotly charts with heat stress monitoring
- **Flexible Configuration**: Supports date ranges and multiple output formats

## Quick Start

### Installation

**Python:**
```bash
cd python
pip install -r requirements.txt
```

**R:**
```r
install.packages(c("optparse", "readr", "dplyr", "lubridate", "plotly", "htmlwidgets", "yaml"))
```

### Configuration

Create or edit `configs/biobasis_merge.yaml`:

```yaml
input_dir: "path/to/input/data"
output_dir: "path/to/output" 
date_start: "20240101"  # YYYYMMDD or YYYY-MM-DD
date_end: "20240131"
```

### Usage

**Python:**
```bash
python -m biobasis_merge_py --config configs/biobasis_merge.yaml
```

**R:**
```bash
Rscript R/R/cli.R --config configs/biobasis_merge.yaml
```

**Options:**
- `--dry-run`: Preview operations without generating outputs
- `--overwrite`: Replace existing output files

## Input Data Format

Input files follow the pattern `Biobasis_MM1_YYYYMMDD.dat` with:
- **4-line header**: metadata, column names, units, statistics
- **30-minute intervals**: TIMESTAMP and meteorological variables
- **Required columns**: BGTemp_C_Avg, AirTC_Avg, RH_Avg, P_Air_Avg

## WBGT Calculations

The tool calculates 5 meteorological parameters using Campbell Scientific formulas:

### Formula
**WBGT = 0.2 × Black Globe + 0.7 × Wet-bulb + 0.1 × Air Temperature**

### Output Parameters
1. **esat_kPa**: Saturated vapor pressure (kPa)
2. **ea_kPa**: Actual vapor pressure (kPa)
3. **dewpoint_C**: Dewpoint temperature (°C)
4. **wet_bulb_C**: Wet-bulb temperature (°C) - iterative calculation
5. **WBGT_C**: Wet-Bulb Globe Temperature heat stress index (°C)

## Outputs

For each processing run, the tool generates:

- **`Biobasis_MM1_merged_{dates}.csv`**: Complete dataset with original + calculated columns
- **`Biobasis_MM1_merged_{dates}_metadata.csv`**: Column metadata (units, statistics)  
- **`Biobasis_MM1_merged_{dates}_plots.html`**: Interactive visualizations including WBGT trends

## Data Processing

The tool automatically:
1. Discovers and loads daily files in the specified date range
2. Creates a complete 30-minute timeline (fills gaps with NaN)
3. Removes duplicate timestamps (keeps first occurrence)
4. Calculates WBGT and related meteorological parameters
5. Generates interactive plots and exports data

## Testing

**Python:**
```bash
cd python
pytest biobasis_merge_py/tests/
```

**R:**
```r
library(testthat)
setwd("R")
test_dir("tests/testthat")
```

## Architecture

```
biobasis_merge/
├── python/biobasis_merge_py/   # Python implementation
│   ├── meteorology.py          # WBGT calculations
│   ├── main.py, cli.py         # Core pipeline & CLI
│   └── tests/                  # Unit tests
├── R/R/                        # R implementation  
│   ├── meteorology.R           # WBGT calculations
│   ├── main.R, cli.R           # Core pipeline & CLI
│   └── tests/                  # R tests
├── configs/                    # Configuration files
└── tests/data/                 # Test data
```

## Scientific References

- Campbell Scientific Black Globe Temperature Manual
- Standard meteorological formulas for vapor pressure calculations
- WBGT heat stress index methodology

## License

[License details]
