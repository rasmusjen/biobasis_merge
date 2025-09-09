"""Command-line interface for biobasis_merge_py."""

import argparse
import sys
from pathlib import Path
from .main import main_pipeline


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Merge daily Biobasis meteorological data files"
    )
    
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually running"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level"
    )
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        main_pipeline(
            config_path=args.config,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            log_level=args.log_level
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
