"""Tests for merge logic functionality."""

import pytest
import pandas as pd
from datetime import datetime
from biobasis_merge_py.merge_logic import (
    concatenate_dataframes, sort_by_timestamp, remove_duplicates,
    create_complete_time_index, reindex_to_complete_grid, merge_daily_data,
    get_merge_summary
)


def create_test_dataframe(timestamps, values, timestamp_col='TIMESTAMP'):
    """Create a test dataframe with given timestamps and values."""
    return pd.DataFrame({
        timestamp_col: pd.to_datetime(timestamps, utc=True),
        'RECORD': range(len(timestamps)),
        'value': values
    })


def test_concatenate_dataframes():
    """Test dataframe concatenation."""
    df1 = create_test_dataframe(['2024-01-01 00:00:00', '2024-01-01 00:30:00'], [1, 2])
    df2 = create_test_dataframe(['2024-01-01 01:00:00', '2024-01-01 01:30:00'], [3, 4])
    
    result = concatenate_dataframes([df1, df2])
    
    assert len(result) == 4
    assert list(result['value']) == [1, 2, 3, 4]


def test_concatenate_empty_list():
    """Test concatenation with empty dataframe list."""
    with pytest.raises(ValueError, match="No dataframes to concatenate"):
        concatenate_dataframes([])


def test_sort_by_timestamp():
    """Test sorting by timestamp."""
    # Create unsorted dataframe
    df = create_test_dataframe(
        ['2024-01-01 01:00:00', '2024-01-01 00:00:00', '2024-01-01 00:30:00'],
        [2, 1, 3]
    )
    
    result = sort_by_timestamp(df, 'TIMESTAMP')
    
    expected_order = [1, 3, 2]  # Values sorted by timestamp
    assert list(result['value']) == expected_order


def test_sort_missing_column():
    """Test sorting with missing timestamp column."""
    df = pd.DataFrame({'value': [1, 2, 3]})
    
    with pytest.raises(ValueError, match="Timestamp column 'TIMESTAMP' not found"):
        sort_by_timestamp(df, 'TIMESTAMP')


def test_remove_duplicates():
    """Test duplicate removal."""
    # Create dataframe with duplicate timestamps
    df = create_test_dataframe(
        ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:30:00'],
        [1, 2, 3]  # First occurrence should be kept
    )
    
    result = remove_duplicates(df, 'TIMESTAMP')
    
    assert len(result) == 2
    assert list(result['value']) == [1, 3]  # First occurrence kept


def test_create_complete_time_index():
    """Test complete time index creation."""
    date_start = datetime(2024, 1, 1)
    date_end = datetime(2024, 1, 1)  # Same day
    
    index = create_complete_time_index(date_start, date_end)
    
    # Should have 48 timestamps for one day (00:00 to 23:30 at 30-min intervals)
    assert len(index) == 48
    assert index[0] == pd.Timestamp('2024-01-01 00:00:00', tz='UTC')
    assert index[-1] == pd.Timestamp('2024-01-01 23:30:00', tz='UTC')


def test_create_complete_time_index_multi_day():
    """Test complete time index for multiple days."""
    date_start = datetime(2024, 1, 1)
    date_end = datetime(2024, 1, 2)  # Two days
    
    index = create_complete_time_index(date_start, date_end)
    
    # Should have 96 timestamps for two days
    assert len(index) == 96
    assert index[0] == pd.Timestamp('2024-01-01 00:00:00', tz='UTC')
    assert index[-1] == pd.Timestamp('2024-01-02 23:30:00', tz='UTC')


def test_reindex_to_complete_grid():
    """Test reindexing to complete 30-minute grid."""
    # Create sparse dataframe
    df = create_test_dataframe(
        ['2024-01-01 00:00:00', '2024-01-01 01:00:00'],  # Missing 00:30
        [1, 2]
    )
    
    date_start = datetime(2024, 1, 1)
    date_end = datetime(2024, 1, 1)
    
    result = reindex_to_complete_grid(df, 'TIMESTAMP', date_start, date_end)
    
    # Should have 48 rows for complete day
    assert len(result) == 48
    
    # Check that missing values are NaN
    assert pd.isna(result.iloc[1]['value'])  # 00:30 should be NaN
    assert result.iloc[0]['value'] == 1      # 00:00 should be 1
    assert result.iloc[2]['value'] == 2      # 01:00 should be 2


def test_merge_daily_data():
    """Test complete merge pipeline."""
    # Create two dataframes with some overlap and gaps
    df1 = create_test_dataframe(
        ['2024-01-01 00:00:00', '2024-01-01 00:30:00', '2024-01-01 01:00:00'],
        [1, 2, 3]
    )
    df2 = create_test_dataframe(
        ['2024-01-01 01:00:00', '2024-01-01 01:30:00'],  # 01:00 is duplicate
        [4, 5]  # 4 should be ignored (duplicate), 5 should be kept
    )
    
    date_start = datetime(2024, 1, 1)
    date_end = datetime(2024, 1, 1)
    
    result = merge_daily_data([df1, df2], date_start, date_end)
    
    # Should have complete day (48 timestamps)
    assert len(result) == 48
    
    # Check specific values
    assert result.iloc[0]['value'] == 1    # 00:00
    assert result.iloc[1]['value'] == 2    # 00:30
    assert result.iloc[2]['value'] == 3    # 01:00 (first occurrence)
    assert result.iloc[3]['value'] == 5    # 01:30


def test_get_merge_summary():
    """Test merge summary generation."""
    # Create test dataframe with some missing data
    df = create_test_dataframe(
        ['2024-01-01 00:00:00', '2024-01-01 00:30:00'],
        [1, None]  # Second value is missing
    )
    # Add more rows to complete a day worth of data
    complete_timestamps = pd.date_range(
        '2024-01-01 00:00:00', '2024-01-01 23:30:00', freq='30T', tz='UTC'
    )
    df = pd.DataFrame({
        'TIMESTAMP': complete_timestamps,
        'value': [1 if i < 2 else None for i in range(len(complete_timestamps))]
    })
    
    date_start = datetime(2024, 1, 1)
    date_end = datetime(2024, 1, 1)
    
    summary = get_merge_summary(df, 'TIMESTAMP', date_start, date_end)
    
    assert summary['total_rows'] == 48
    assert summary['expected_rows'] == 48
    assert summary['timestamp_column'] == 'TIMESTAMP'
    assert 'data_coverage' in summary
    assert 'date_range' in summary


def test_merge_empty_dataframes():
    """Test merge with empty dataframe list."""
    with pytest.raises(ValueError, match="No dataframes provided"):
        merge_daily_data([], datetime(2024, 1, 1), datetime(2024, 1, 1))
