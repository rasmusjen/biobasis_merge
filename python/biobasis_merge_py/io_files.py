"""File I/O operations for reading and discovering Biobasis data files."""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import logging
from .parse_header import parse_header, get_timestamp_column_info

logger = logging.getLogger(__name__)


def build_expected_file_list(input_dir: str, date_start: datetime, date_end: datetime) -> List[Tuple[datetime, str]]:
    """Build list of expected daily files in date range."""
    from .utils import generate_date_list
    
    input_path = Path(input_dir)
    expected_files = []
    
    for date in generate_date_list(date_start, date_end):
        date_str = date.strftime('%Y%m%d')
        filename = f"Biobasis_MM1_{date_str}.dat"
        file_path = input_path / filename
        expected_files.append((date, str(file_path)))
    
    return expected_files


def check_file_existence(file_list: List[Tuple[datetime, str]]) -> Tuple[List[Tuple[datetime, str]], List[Tuple[datetime, str]]]:
    """Check which files exist and return (existing, missing) lists."""
    existing = []
    missing = []
    
    for date, file_path in file_list:
        if Path(file_path).exists():
            existing.append((date, file_path))
        else:
            missing.append((date, file_path))
    
    logger.info(f"Found {len(existing)} existing files, {len(missing)} missing files")
    return existing, missing


def read_data_file(file_path: str) -> Tuple[pd.DataFrame, Dict[str, str], Dict[str, str]]:
    """
    Read a single Biobasis data file.
    
    Returns:
        Tuple of (dataframe, units_dict, stats_dict)
    """
    try:
        # Parse header first
        column_names, units_dict, stats_dict = parse_header(file_path)
        
        # Read data starting from line 5 (0-indexed line 4)
        df = pd.read_csv(
            file_path,
            skiprows=4,
            names=column_names,
            parse_dates=False,  # We'll handle timestamp parsing separately
            dtype=str  # Read all columns as strings first to avoid conversion errors
        )
        
        # Parse timestamp column
        timestamp_col = get_timestamp_column_info(column_names)
        
        if timestamp_col in df.columns:
            # Convert timestamp to datetime without timezone info
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        
        # Convert numeric columns, handling errors gracefully
        for col in df.columns:
            if col != timestamp_col:  # Skip timestamp column
                # Try to convert to numeric, keeping as string if it fails
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                # Only convert if we have at least some valid numeric values
                if not numeric_series.isna().all():
                    df[col] = numeric_series
        
        logger.debug(f"Read {len(df)} rows from {file_path}")
        return df, units_dict, stats_dict
        
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def load_all_files(file_list: List[Tuple[datetime, str]]) -> Tuple[List[pd.DataFrame], List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Load all existing data files.
    
    Returns:
        Tuple of (dataframes_list, units_list, stats_list)
    """
    dataframes = []
    units_list = []
    stats_list = []
    
    for date, file_path in file_list:
        try:
            df, units_dict, stats_dict = read_data_file(file_path)
            dataframes.append(df)
            units_list.append(units_dict)
            stats_list.append(stats_dict)
            logger.debug(f"Successfully loaded {file_path}")
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            continue
    
    logger.info(f"Successfully loaded {len(dataframes)} files")
    return dataframes, units_list, stats_list


def validate_output_paths(output_dir: str, date_range: str, overwrite: bool = False) -> Dict[str, str]:
    """
    Validate output file paths and check for existing files.
    
    Returns:
        Dictionary of output file paths
    """
    output_path = Path(output_dir)
    base_name = f"Biobasis_MM1_merged_{date_range}"
    
    output_files = {
        'csv': str(output_path / f"{base_name}.csv"),
        'metadata': str(output_path / f"{base_name}_metadata.csv"),
        'plots': str(output_path / f"{base_name}_plots.html")
    }
    
    # Check for existing files
    existing_files = []
    for file_type, file_path in output_files.items():
        if Path(file_path).exists():
            existing_files.append(file_path)
    
    if existing_files and not overwrite:
        raise FileExistsError(
            f"Output files already exist: {existing_files}. "
            "Use --overwrite to overwrite existing files."
        )
    
    return output_files
