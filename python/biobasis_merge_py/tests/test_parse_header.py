"""Tests for header parsing functionality."""

import pytest
import tempfile
from pathlib import Path
from biobasis_merge_py.parse_header import (
    parse_header, validate_header_consistency, get_timestamp_column_info
)


def create_test_file(content: str) -> str:
    """Create a temporary test file with given content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.dat') as f:
        f.write(content)
        return f.name


def test_parse_header_valid():
    """Test parsing of valid header."""
    content = '''TOA5,Biobasis_MM1,CR6,12345,CR6.Std.03.02,CPU:Biobasis.CR6,12345,Biobasis_MM1
TIMESTAMP,RECORD,AirTC_Avg,RH_Avg,WS_ms_Avg,WindDir_D1_WVT
TS,RN,Deg C,%,m/s,Deg
Avg,Avg,Avg,Avg,Avg,Avg
2024-01-01 00:00:00,0,15.2,65.5,2.1,180
'''
    
    file_path = create_test_file(content)
    
    try:
        columns, units, stats = parse_header(file_path)
        
        expected_columns = ['TIMESTAMP', 'RECORD', 'AirTC_Avg', 'RH_Avg', 'WS_ms_Avg', 'WindDir_D1_WVT']
        expected_units = {
            'TIMESTAMP': 'TS',
            'RECORD': 'RN', 
            'AirTC_Avg': 'Deg C',
            'RH_Avg': '%',
            'WS_ms_Avg': 'm/s',
            'WindDir_D1_WVT': 'Deg'
        }
        expected_stats = {
            'TIMESTAMP': 'Avg',
            'RECORD': 'Avg',
            'AirTC_Avg': 'Avg',
            'RH_Avg': 'Avg', 
            'WS_ms_Avg': 'Avg',
            'WindDir_D1_WVT': 'Avg'
        }
        
        assert columns == expected_columns
        assert units == expected_units
        assert stats == expected_stats
        
    finally:
        Path(file_path).unlink()


def test_parse_header_quoted_values():
    """Test parsing header with quoted values."""
    content = '''TOA5,Biobasis_MM1,CR6,12345,CR6.Std.03.02,CPU:Biobasis.CR6,12345,Biobasis_MM1
"TIMESTAMP","RECORD","AirTC_Avg","RH_Avg"
"TS","RN","Deg C","%"
"Avg","Avg","Avg","Avg"
2024-01-01 00:00:00,0,15.2,65.5
'''
    
    file_path = create_test_file(content)
    
    try:
        columns, units, stats = parse_header(file_path)
        
        expected_columns = ['TIMESTAMP', 'RECORD', 'AirTC_Avg', 'RH_Avg']
        assert columns == expected_columns
        assert units['AirTC_Avg'] == 'Deg C'
        assert units['RH_Avg'] == '%'
        
    finally:
        Path(file_path).unlink()


def test_parse_header_insufficient_lines():
    """Test parsing header with insufficient lines."""
    content = '''TOA5,Biobasis_MM1,CR6,12345,CR6.Std.03.02,CPU:Biobasis.CR6,12345,Biobasis_MM1
TIMESTAMP,RECORD,AirTC_Avg
'''
    
    file_path = create_test_file(content)
    
    try:
        with pytest.raises(ValueError, match="fewer than 4 header lines"):
            parse_header(file_path)
    finally:
        Path(file_path).unlink()


def test_parse_header_mismatched_lengths():
    """Test parsing header with mismatched column/unit/stat lengths."""
    content = '''TOA5,Biobasis_MM1,CR6,12345,CR6.Std.03.02,CPU:Biobasis.CR6,12345,Biobasis_MM1
TIMESTAMP,RECORD,AirTC_Avg
TS,RN
Avg
2024-01-01 00:00:00,0,15.2
'''
    
    file_path = create_test_file(content)
    
    try:
        columns, units, stats = parse_header(file_path)
        
        # Should handle mismatched lengths gracefully
        assert len(columns) == 3
        assert units['AirTC_Avg'] == ""  # No unit provided
        assert stats['RECORD'] == ""     # No stat provided
        
    finally:
        Path(file_path).unlink()


def test_validate_header_consistency():
    """Test header consistency validation."""
    headers = [
        (['TIMESTAMP', 'RECORD', 'AirTC_Avg'], {'TIMESTAMP': 'TS'}, {'TIMESTAMP': 'Avg'}),
        (['TIMESTAMP', 'RECORD', 'AirTC_Avg'], {'TIMESTAMP': 'TS'}, {'TIMESTAMP': 'Avg'}),
        (['TIMESTAMP', 'RECORD', 'RH_Avg'], {'TIMESTAMP': 'TS'}, {'TIMESTAMP': 'Avg'})  # Different columns
    ]
    
    # Should not raise exception, but may log warnings
    validate_header_consistency(headers)


def test_get_timestamp_column_info():
    """Test timestamp column identification."""
    # Standard timestamp column
    columns = ['TIMESTAMP', 'RECORD', 'AirTC_Avg']
    assert get_timestamp_column_info(columns) == 'TIMESTAMP'
    
    # Lowercase timestamp
    columns = ['timestamp', 'record', 'temp']
    assert get_timestamp_column_info(columns) == 'timestamp'
    
    # DateTime column
    columns = ['DateTime', 'RECORD', 'temp']
    assert get_timestamp_column_info(columns) == 'DateTime'
    
    # No standard timestamp column - should use first column
    columns = ['time_col', 'RECORD', 'temp']
    assert get_timestamp_column_info(columns) == 'time_col'
    
    # Empty columns
    with pytest.raises(ValueError, match="No columns found"):
        get_timestamp_column_info([])
