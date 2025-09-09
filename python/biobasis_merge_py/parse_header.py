"""Header parsing for Biobasis data files."""

import pandas as pd
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def parse_header(file_path: str) -> Tuple[List[str], Dict[str, str], Dict[str, str]]:
    """
    Parse 4-line header from Biobasis data file.
    
    Returns:
        Tuple of (column_names, units_dict, stats_dict)
    """
    try:
        with open(file_path, 'r') as f:
            lines = [f.readline().strip() for _ in range(4)]
        
        if len(lines) < 4:
            raise ValueError(f"File {file_path} has fewer than 4 header lines")
        
        # Line 2: Column names (split by comma)
        column_names = [col.strip('"') for col in lines[1].split(',')]
        
        # Line 3: Units (split by comma)
        units_list = [unit.strip('"') for unit in lines[2].split(',')]
        
        # Line 4: Statistics (split by comma)
        stats_list = [stat.strip('"') for stat in lines[3].split(',')]
        
        # Create dictionaries mapping column names to units/stats
        units_dict = {}
        stats_dict = {}
        
        for i, col_name in enumerate(column_names):
            if i < len(units_list):
                units_dict[col_name] = units_list[i]
            else:
                units_dict[col_name] = ""
                
            if i < len(stats_list):
                stats_dict[col_name] = stats_list[i]
            else:
                stats_dict[col_name] = ""
        
        logger.debug(f"Parsed header from {file_path}: {len(column_names)} columns")
        return column_names, units_dict, stats_dict
        
    except Exception as e:
        logger.error(f"Error parsing header from {file_path}: {e}")
        raise


def validate_header_consistency(headers: List[Tuple[List[str], Dict[str, str], Dict[str, str]]]) -> None:
    """Validate that all headers have consistent column structure."""
    if not headers:
        return
    
    reference_columns = headers[0][0]
    
    for i, (columns, _, _) in enumerate(headers[1:], 1):
        if columns != reference_columns:
            logger.warning(f"Header {i} has different columns than reference header")
            # Log the differences
            ref_set = set(reference_columns)
            curr_set = set(columns)
            missing = ref_set - curr_set
            extra = curr_set - ref_set
            if missing:
                logger.warning(f"Missing columns: {missing}")
            if extra:
                logger.warning(f"Extra columns: {extra}")


def get_timestamp_column_info(column_names: List[str]) -> str:
    """Find the timestamp column name."""
    timestamp_candidates = ['TIMESTAMP', 'timestamp', 'DateTime', 'datetime', 'TIME', 'time']
    
    for candidate in timestamp_candidates:
        if candidate in column_names:
            return candidate
    
    # If no standard timestamp column found, assume first column
    if column_names:
        logger.warning(f"No standard timestamp column found, using first column: {column_names[0]}")
        return column_names[0]
    
    raise ValueError("No columns found in header")
