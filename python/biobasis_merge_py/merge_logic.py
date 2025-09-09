"""Data merging and reindexing logic."""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple
import logging
from .parse_header import get_timestamp_column_info

logger = logging.getLogger(__name__)


def concatenate_dataframes(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate all dataframes into a single dataframe."""
    if not dataframes:
        raise ValueError("No dataframes to concatenate")
    
    # Concatenate all dataframes
    merged_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Concatenated {len(dataframes)} dataframes into {len(merged_df)} rows")
    
    return merged_df


def sort_by_timestamp(df: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
    """Sort dataframe by timestamp column."""
    if timestamp_col not in df.columns:
        raise ValueError(f"Timestamp column '{timestamp_col}' not found in dataframe")
    
    sorted_df = df.sort_values(by=timestamp_col).reset_index(drop=True)
    logger.debug(f"Sorted dataframe by {timestamp_col}")
    
    return sorted_df


def remove_duplicates(df: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
    """Remove duplicate timestamps, keeping the first occurrence."""
    initial_length = len(df)
    
    # Remove duplicates based on timestamp column, keeping first occurrence
    deduped_df = df.drop_duplicates(subset=[timestamp_col], keep='first').reset_index(drop=True)
    
    duplicates_removed = initial_length - len(deduped_df)
    if duplicates_removed > 0:
        logger.warning(f"Removed {duplicates_removed} duplicate timestamps")
    
    return deduped_df


def create_complete_time_index(date_start: datetime, date_end: datetime, freq: str = '30T') -> pd.DatetimeIndex:
    """
    Create complete time index from start 00:00:00 to end 23:30:00 at specified frequency.
    
    Args:
        date_start: Start date
        date_end: End date
        freq: Frequency string (e.g., '30T' for 30 minutes)
    """
    # Create start and end timestamps
    start_timestamp = pd.Timestamp(date_start.replace(hour=0, minute=0, second=0))
    end_timestamp = pd.Timestamp(date_end.replace(hour=23, minute=30, second=0))
    
    # Create complete time index
    complete_index = pd.date_range(
        start=start_timestamp,
        end=end_timestamp,
        freq=freq.replace('T', 'min') if 'T' in freq else freq
    )
    
    logger.info(f"Created complete time index with {len(complete_index)} timestamps")
    return complete_index


def reindex_to_complete_grid(df: pd.DataFrame, timestamp_col: str, date_start: datetime, date_end: datetime) -> pd.DataFrame:
    """
    Reindex dataframe to complete 30-minute grid, filling missing values with NaN.
    """
    if timestamp_col not in df.columns:
        raise ValueError(f"Timestamp column '{timestamp_col}' not found in dataframe")
    
    # Create complete time index
    complete_index = create_complete_time_index(date_start, date_end)
    
    # Set timestamp as index
    df_indexed = df.set_index(timestamp_col)
    
    # Reindex to complete grid
    reindexed_df = df_indexed.reindex(complete_index)
    
    # Reset index to make timestamp a column again
    reindexed_df = reindexed_df.reset_index()
    reindexed_df = reindexed_df.rename(columns={'index': timestamp_col})
    
    missing_count = reindexed_df.isnull().sum().sum()
    logger.info(f"Reindexed to complete grid: {len(reindexed_df)} timestamps, {missing_count} missing values")
    
    return reindexed_df


def merge_daily_data(dataframes: List[pd.DataFrame], date_start: datetime, date_end: datetime) -> pd.DataFrame:
    """
    Complete data merging pipeline.
    
    Steps:
    1. Concatenate all dataframes
    2. Sort by timestamp
    3. Remove duplicates (keep first)
    4. Reindex to complete 30-minute grid
    """
    if not dataframes:
        raise ValueError("No dataframes provided for merging")
    
    # Get timestamp column name from first dataframe
    timestamp_col = get_timestamp_column_info(list(dataframes[0].columns))
    
    logger.info("Starting data merge pipeline")
    
    # Step 1: Concatenate
    merged_df = concatenate_dataframes(dataframes)
    
    # Step 2: Sort by timestamp
    merged_df = sort_by_timestamp(merged_df, timestamp_col)
    
    # Step 3: Remove duplicates
    merged_df = remove_duplicates(merged_df, timestamp_col)
    
    # Step 4: Reindex to complete grid
    merged_df = reindex_to_complete_grid(merged_df, timestamp_col, date_start, date_end)
    
    logger.info("Data merge pipeline completed successfully")
    return merged_df


def get_merge_summary(df: pd.DataFrame, timestamp_col: str, date_start: datetime, date_end: datetime) -> dict:
    """Generate summary statistics for merged data."""
    complete_index = create_complete_time_index(date_start, date_end)
    expected_rows = len(complete_index)
    actual_rows = len(df)
    
    # Count missing timestamps (rows with all NaN except timestamp)
    data_cols = [col for col in df.columns if col != timestamp_col]
    missing_timestamps = df[data_cols].isnull().all(axis=1).sum()
    
    summary = {
        'total_rows': actual_rows,
        'expected_rows': expected_rows,
        'missing_timestamps': missing_timestamps,
        'data_coverage': (actual_rows - missing_timestamps) / expected_rows * 100,
        'timestamp_column': timestamp_col,
        'date_range': f"{date_start.strftime('%Y-%m-%d')} to {date_end.strftime('%Y-%m-%d')}"
    }
    
    return summary
