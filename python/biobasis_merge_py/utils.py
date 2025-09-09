"""Utilities for configuration parsing, date handling, and logging setup."""

import logging
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_config(config_path: str) -> Dict[str, Any]:
    """Parse YAML configuration file."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required_fields = ['input_dir', 'output_dir', 'date_start', 'date_end']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Required field '{field}' missing from configuration")
    
    return config


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYYMMDD or YYYY-MM-DD format."""
    # Try YYYYMMDD format first
    try:
        return datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        pass
    
    # Try YYYY-MM-DD format
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYYMMDD or YYYY-MM-DD")


def format_date_range(date_start: datetime, date_end: datetime) -> str:
    """Format date range as YYYYMMDD-YYYYMMDD string."""
    start_str = date_start.strftime('%Y%m%d')
    end_str = date_end.strftime('%Y%m%d')
    return f"{start_str}-{end_str}"


def generate_date_list(date_start: datetime, date_end: datetime) -> List[datetime]:
    """Generate list of dates from start to end (inclusive)."""
    dates = []
    current_date = date_start
    while current_date <= date_end:
        dates.append(current_date)
        current_date += timedelta(days=1)
    return dates


def validate_output_dir(output_dir: str, create: bool = True) -> Path:
    """Validate and optionally create output directory."""
    output_path = Path(output_dir)
    if create:
        output_path.mkdir(parents=True, exist_ok=True)
    return output_path
