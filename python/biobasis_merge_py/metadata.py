"""Metadata consolidation across multiple files."""

import pandas as pd
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def consolidate_metadata(units_list: List[Dict[str, str]], stats_list: List[Dict[str, str]]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Consolidate units and statistics metadata across multiple files.
    
    Strategy: For each column, use the first non-empty/non-NA value encountered.
    """
    if not units_list or not stats_list:
        return {}, {}
    
    # Get all unique column names
    all_columns = set()
    for units_dict in units_list:
        all_columns.update(units_dict.keys())
    for stats_dict in stats_list:
        all_columns.update(stats_dict.keys())
    
    consolidated_units = {}
    consolidated_stats = {}
    
    # For each column, find first non-empty unit and stat
    for column in all_columns:
        # Consolidate units
        unit_value = ""
        for units_dict in units_list:
            if column in units_dict and units_dict[column] and units_dict[column].strip():
                unit_value = units_dict[column].strip()
                break
        consolidated_units[column] = unit_value
        
        # Consolidate stats
        stat_value = ""
        for stats_dict in stats_list:
            if column in stats_dict and stats_dict[column] and stats_dict[column].strip():
                stat_value = stats_dict[column].strip()
                break
        consolidated_stats[column] = stat_value
    
    logger.info(f"Consolidated metadata for {len(all_columns)} columns")
    return consolidated_units, consolidated_stats


def create_metadata_dataframe(units_dict: Dict[str, str], stats_dict: Dict[str, str]) -> pd.DataFrame:
    """Create a tidy metadata dataframe from units and stats dictionaries."""
    
    # Get all columns
    all_columns = set(units_dict.keys()) | set(stats_dict.keys())
    
    metadata_rows = []
    for column in sorted(all_columns):
        unit = units_dict.get(column, "")
        stat = stats_dict.get(column, "")
        
        metadata_rows.append({
            'column_name': column,
            'unit': unit,
            'statistic': stat
        })
    
    metadata_df = pd.DataFrame(metadata_rows)
    logger.debug(f"Created metadata dataframe with {len(metadata_df)} rows")
    
    return metadata_df


def validate_metadata_consistency(units_list: List[Dict[str, str]], stats_list: List[Dict[str, str]]) -> None:
    """Validate metadata consistency across files and log warnings for inconsistencies."""
    
    if len(units_list) != len(stats_list):
        logger.warning(f"Mismatch in metadata list lengths: {len(units_list)} units vs {len(stats_list)} stats")
    
    if len(units_list) <= 1:
        return  # No comparison possible
    
    # Check for inconsistent units
    column_units = {}
    for i, units_dict in enumerate(units_list):
        for column, unit in units_dict.items():
            if unit and unit.strip():  # Only consider non-empty units
                if column not in column_units:
                    column_units[column] = []
                column_units[column].append((i, unit.strip()))
    
    # Check for inconsistent stats
    column_stats = {}
    for i, stats_dict in enumerate(stats_list):
        for column, stat in stats_dict.items():
            if stat and stat.strip():  # Only consider non-empty stats
                if column not in column_stats:
                    column_stats[column] = []
                column_stats[column].append((i, stat.strip()))
    
    # Report inconsistencies
    for column, unit_values in column_units.items():
        unique_units = set(unit for _, unit in unit_values)
        if len(unique_units) > 1:
            logger.warning(f"Column '{column}' has inconsistent units across files: {unique_units}")
    
    for column, stat_values in column_stats.items():
        unique_stats = set(stat for _, stat in stat_values)
        if len(unique_stats) > 1:
            logger.warning(f"Column '{column}' has inconsistent statistics across files: {unique_stats}")


def save_metadata(metadata_df: pd.DataFrame, output_path: str) -> None:
    """Save metadata dataframe to CSV file."""
    try:
        metadata_df.to_csv(output_path, index=False)
        logger.info(f"Saved metadata to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save metadata to {output_path}: {e}")
        raise
