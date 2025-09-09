"""Simple tests for biobasis_merge_py package."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

from biobasis_merge_py.utils import setup_logging, parse_config
from biobasis_merge_py.parse_header import parse_header


class TestUtils:
    """Test utility functions."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        # Test that setup_logging doesn't raise an error
        setup_logging('DEBUG')
        setup_logging('INFO')
        # Basic test - if it doesn't crash, it works
        assert True
    
    def test_parse_config(self):
        """Test configuration parsing."""
        # Create a temporary config file
        import tempfile
        import os
        
        valid_config = {
            'input_dir': 'tests/data',
            'output_dir': 'data/output',
            'date_start': '20240101',
            'date_end': '20240103',
            'station_id': 'MM1',
            'file_prefix': 'Biobasis',
            'log_level': 'INFO'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(valid_config, f)
            temp_config_path = f.name
        
        try:
            # Should not raise any exception
            config = parse_config(temp_config_path)
            assert config['input_dir'] == 'tests/data'
            assert config['station_id'] == 'MM1'
        finally:
            os.unlink(temp_config_path)
        
        # Test missing file
        with pytest.raises(FileNotFoundError):
            parse_config('nonexistent.yaml')


class TestParseHeader:
    """Test header parsing functionality."""
    
    def test_parse_header(self):
        """Test header parsing with sample data."""
        # Use one of our test files
        test_file = Path("tests/data/Biobasis_MM1_20240101.dat")
        assert test_file.exists(), "Test file should exist for this test"
        
        column_names, units_dict, stats_dict = parse_header(str(test_file))
        
        # Check that we got reasonable results
        assert isinstance(column_names, list)
        assert len(column_names) >= 5  # Should have at least 5 columns
        assert 'TIMESTAMP' in column_names
        assert 'RECORD' in column_names
        
        # Check that units and stats are dictionaries
        assert isinstance(units_dict, dict)
        assert isinstance(stats_dict, dict)
        
        # Check that they have entries for all columns
        assert len(units_dict) == len(column_names)
        assert len(stats_dict) == len(column_names)


class TestIntegration:
    """Integration tests."""
    
    def test_package_import(self):
        """Test that all modules can be imported."""
        import biobasis_merge_py
        import biobasis_merge_py.utils
        import biobasis_merge_py.io_files
        import biobasis_merge_py.parse_header
        import biobasis_merge_py.merge_logic
        import biobasis_merge_py.metadata
        import biobasis_merge_py.plots
        
        # If we get here, all imports worked
        assert True
    
    def test_test_data_exists(self):
        """Test that our test data files exist."""
        test_dir = Path("tests/data")
        assert test_dir.exists(), "Test data directory should exist"
        
        # Check for our test files
        file1 = test_dir / "Biobasis_MM1_20240101.dat"
        file2 = test_dir / "Biobasis_MM1_20240102.dat"
        
        assert file1.exists(), "Test file 1 should exist"
        assert file2.exists(), "Test file 2 should exist"
        
        # Check that test file 3 doesn't exist (this is intentional for testing missing files)
        file3 = test_dir / "Biobasis_MM1_20240103.dat"
        assert not file3.exists(), "Test file 3 should NOT exist (for testing missing file handling)"


if __name__ == "__main__":
    pytest.main([__file__])
