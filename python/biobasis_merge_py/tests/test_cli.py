"""Tests for CLI functionality."""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch
from biobasis_merge_py.cli import create_parser, main
from biobasis_merge_py.main import main_pipeline


def test_create_parser():
    """Test argument parser creation."""
    parser = create_parser()
    
    # Test required config argument
    with pytest.raises(SystemExit):
        parser.parse_args([])
    
    # Test valid arguments
    args = parser.parse_args(['--config', 'test.yaml'])
    assert args.config == 'test.yaml'
    assert args.dry_run is False
    assert args.overwrite is False
    assert args.log_level == 'INFO'
    
    # Test optional arguments
    args = parser.parse_args(['--config', 'test.yaml', '--dry-run', '--overwrite', '--log-level', 'DEBUG'])
    assert args.dry_run is True
    assert args.overwrite is True
    assert args.log_level == 'DEBUG'


def test_cli_main_with_missing_config():
    """Test CLI main function with missing config file."""
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
        config_path = f.name
    
    # Delete the file so it doesn't exist
    Path(config_path).unlink()
    
    with patch('sys.argv', ['biobasis_merge_py', '--config', config_path]):
        with pytest.raises(SystemExit):
            main()


def test_cli_dry_run():
    """Test CLI dry run functionality."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            'input_dir': '/nonexistent/input',
            'output_dir': '/tmp/output',
            'date_start': '20240101',
            'date_end': '20240102'
        }
        yaml.dump(config, f)
        config_path = f.name
    
    try:
        # This should not raise an exception even with nonexistent input dir
        main_pipeline(config_path, dry_run=True)
    finally:
        Path(config_path).unlink()


def test_cli_validation_errors():
    """Test CLI validation with invalid configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            'input_dir': '/nonexistent/input',
            'output_dir': '/tmp/output',
            'date_start': '20240101',
            'date_end': '20240102'
        }
        yaml.dump(config, f)
        config_path = f.name
    
    try:
        with pytest.raises(ValueError, match="No input files found"):
            main_pipeline(config_path, dry_run=False)
    finally:
        Path(config_path).unlink()
