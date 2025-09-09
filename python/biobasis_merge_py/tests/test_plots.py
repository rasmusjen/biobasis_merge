"""Tests for plot generation functionality."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from biobasis_merge_py.plots import (
    determine_plot_columns, calculate_subplot_layout, downsample_data,
    create_time_series_plots, validate_plot_output
)


def test_determine_plot_columns():
    """Test plot column determination."""
    df = pd.DataFrame({
        'TIMESTAMP': pd.date_range('2024-01-01', periods=10, freq='30T'),
        'RECORD': range(10),
        'temperature': [20.1, 20.2, 20.3] * 3 + [20.1],
        'humidity': [65.5, 66.0, 65.8] * 3 + [65.5],
        'text_col': ['a', 'b', 'c'] * 3 + ['a']
    })
    
    plot_columns = determine_plot_columns(df)
    
    # Should exclude TIMESTAMP, RECORD, and text columns
    expected = ['temperature', 'humidity']
    assert set(plot_columns) == set(expected)


def test_determine_plot_columns_custom_exclude():
    """Test plot column determination with custom exclusions."""
    df = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=5, freq='30T'),
        'value1': [1, 2, 3, 4, 5],
        'value2': [10, 20, 30, 40, 50],
        'exclude_me': [100, 200, 300, 400, 500]
    })
    
    plot_columns = determine_plot_columns(df, exclude_columns=['time', 'exclude_me'])
    
    expected = ['value1', 'value2']
    assert set(plot_columns) == set(expected)


def test_calculate_subplot_layout():
    """Test subplot layout calculation."""
    # Test various numbers of plots
    assert calculate_subplot_layout(0) == (1, 1)
    assert calculate_subplot_layout(1) == (1, 1)
    assert calculate_subplot_layout(2) == (1, 2)
    assert calculate_subplot_layout(3) == (2, 2)
    assert calculate_subplot_layout(4) == (2, 2)
    assert calculate_subplot_layout(5) == (3, 2)
    
    # Test with custom max columns
    assert calculate_subplot_layout(3, max_cols=3) == (1, 3)
    assert calculate_subplot_layout(4, max_cols=3) == (2, 3)


def test_downsample_data():
    """Test data downsampling."""
    # Create large dataframe
    df = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=1000, freq='1T'),
        'value': range(1000)
    })
    
    # Test no downsampling needed
    result = downsample_data(df, max_points=2000)
    assert len(result) == 1000
    
    # Test downsampling
    result = downsample_data(df, max_points=100)
    assert len(result) <= 100
    assert len(result) > 0


def test_create_time_series_plots():
    """Test time series plot creation."""
    # Create test dataframe
    df = pd.DataFrame({
        'TIMESTAMP': pd.date_range('2024-01-01', periods=48, freq='30T', tz='UTC'),
        'RECORD': range(48),
        'temperature': [20 + i * 0.1 for i in range(48)],
        'humidity': [65 + i * 0.2 for i in range(48)]
    })
    
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        output_path = f.name
    
    try:
        create_time_series_plots(df, 'TIMESTAMP', output_path)
        
        # Check that file was created
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 0
        
        # Validate plot output
        assert validate_plot_output(output_path)
        
    finally:
        Path(output_path).unlink()


def test_create_time_series_plots_no_data():
    """Test plot creation with no numeric columns."""
    df = pd.DataFrame({
        'TIMESTAMP': pd.date_range('2024-01-01', periods=10, freq='30T', tz='UTC'),
        'RECORD': range(10),
        'text_col': ['a'] * 10
    })
    
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        output_path = f.name
    
    try:
        create_time_series_plots(df, 'TIMESTAMP', output_path)
        
        # Should still create a file with "no data" message
        assert Path(output_path).exists()
        
    finally:
        Path(output_path).unlink()


def test_create_time_series_plots_all_nan():
    """Test plot creation with all NaN values."""
    df = pd.DataFrame({
        'TIMESTAMP': pd.date_range('2024-01-01', periods=10, freq='30T', tz='UTC'),
        'RECORD': range(10),
        'temperature': [float('nan')] * 10
    })
    
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        output_path = f.name
    
    try:
        create_time_series_plots(df, 'TIMESTAMP', output_path)
        
        # Should create file even with all NaN data
        assert Path(output_path).exists()
        
    finally:
        Path(output_path).unlink()


def test_validate_plot_output():
    """Test plot output validation."""
    # Test non-existent file
    assert not validate_plot_output('/nonexistent/file.html')
    
    # Test empty file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        empty_file = f.name
    
    try:
        assert not validate_plot_output(empty_file)
    finally:
        Path(empty_file).unlink()
    
    # Test valid HTML file with plotly content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write('<html><head><script src="plotly.js"></script></head></html>')
        valid_file = f.name
    
    try:
        assert validate_plot_output(valid_file)
    finally:
        Path(valid_file).unlink()
    
    # Test invalid HTML file without plotly
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write('<html><head></head><body>No plotly here</body></html>')
        invalid_file = f.name
    
    try:
        assert not validate_plot_output(invalid_file)
    finally:
        Path(invalid_file).unlink()
