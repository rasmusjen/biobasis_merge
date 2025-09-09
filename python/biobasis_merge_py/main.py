"""Main orchestration pipeline for biobasis_merge_py."""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

from .utils import setup_logging, parse_config, parse_date, format_date_range, validate_output_dir
from .io_files import (
    build_expected_file_list, check_file_existence, load_all_files, validate_output_paths
)
from .merge_logic import merge_daily_data, get_merge_summary
from .metadata import consolidate_metadata, create_metadata_dataframe, save_metadata, validate_metadata_consistency
from .plots import create_time_series_plots, create_summary_plot, validate_plot_output
from .parse_header import get_timestamp_column_info
from .meteorology import add_meteorological_calculations

logger = logging.getLogger(__name__)


def save_merged_data(df, output_files: dict) -> None:
    """Save merged data in multiple formats."""
    try:
        # Prepare dataframe for output
        output_df = df.copy()
        
        # Format timestamp column to simple format (no timezone)
        timestamp_cols = [col for col in output_df.columns if 'TIMESTAMP' in col.upper()]
        for col in timestamp_cols:
            if pd.api.types.is_datetime64_any_dtype(output_df[col]):
                output_df[col] = output_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Save as uncompressed CSV with explicit NaN handling
        output_df.to_csv(output_files['csv'], index=False, na_rep='NaN')
        logger.info(f"Saved CSV file: {output_files['csv']}")
        
    except Exception as e:
        logger.error(f"Failed to save merged data: {e}")
        raise


def print_processing_summary(config: dict, existing_files: list, missing_files: list, 
                           merge_summary: dict, output_files: dict) -> None:
    """Print comprehensive processing summary."""
    print("\n" + "="*60)
    print("BIOBASIS MERGE PROCESSING SUMMARY")
    print("="*60)
    
    print(f"\nConfiguration:")
    print(f"  Input directory: {config['input_dir']}")
    print(f"  Output directory: {config['output_dir']}")
    print(f"  Date range: {config['date_start']} to {config['date_end']}")
    
    print(f"\nFile Discovery:")
    print(f"  Expected files: {len(existing_files) + len(missing_files)}")
    print(f"  Found files: {len(existing_files)}")
    print(f"  Missing files: {len(missing_files)}")
    
    if missing_files:
        print(f"  Missing file dates: {[date.strftime('%Y%m%d') for date, _ in missing_files[:5]]}")
        if len(missing_files) > 5:
            print(f"    ... and {len(missing_files) - 5} more")
    
    print(f"\nData Processing:")
    print(f"  Total rows: {merge_summary['total_rows']:,}")
    print(f"  Expected rows: {merge_summary['expected_rows']:,}")
    print(f"  Missing timestamps: {merge_summary['missing_timestamps']:,}")
    print(f"  Data coverage: {merge_summary['data_coverage']:.1f}%")
    print(f"  Timestamp column: {merge_summary['timestamp_column']}")
    
    print(f"\nOutput Files:")
    for file_type, file_path in output_files.items():
        file_exists = Path(file_path).exists()
        status = "✓" if file_exists else "✗"
        print(f"  {status} {file_type.upper()}: {file_path}")
    
    print("\n" + "="*60)


def main_pipeline(config_path: str, dry_run: bool = False, overwrite: bool = False, log_level: str = "INFO") -> None:
    """Main processing pipeline."""
    
    # Setup logging
    setup_logging(log_level)
    logger.info("Starting Biobasis merge pipeline")
    
    try:
        # Load configuration
        config = parse_config(config_path)
        logger.info(f"Loaded configuration from {config_path}")
        
        # Parse dates
        date_start = parse_date(config['date_start'])
        date_end = parse_date(config['date_end'])
        date_range = format_date_range(date_start, date_end)
        
        logger.info(f"Processing date range: {date_start.strftime('%Y-%m-%d')} to {date_end.strftime('%Y-%m-%d')}")
        
        # Validate and create output directory
        output_dir = validate_output_dir(config['output_dir'], create=not dry_run)
        
        # Validate output file paths
        output_files = validate_output_paths(config['output_dir'], date_range, overwrite)
        
        # Build expected file list
        expected_files = build_expected_file_list(config['input_dir'], date_start, date_end)
        
        # Check file existence
        existing_files, missing_files = check_file_existence(expected_files)
        
        if not existing_files:
            raise ValueError("No input files found in the specified date range")
        
        if dry_run:
            print(f"\nDRY RUN - Would process {len(existing_files)} files")
            print(f"Missing {len(missing_files)} files")
            print(f"Output files would be created in: {config['output_dir']}")
            return
        
        # Load all data files
        dataframes, units_list, stats_list = load_all_files(existing_files)
        
        if not dataframes:
            raise ValueError("Failed to load any data files")
        
        # Validate metadata consistency
        validate_metadata_consistency(units_list, stats_list)
        
        # Consolidate metadata
        consolidated_units, consolidated_stats = consolidate_metadata(units_list, stats_list)
        metadata_df = create_metadata_dataframe(consolidated_units, consolidated_stats)
        
        # Merge data
        merged_df = merge_daily_data(dataframes, date_start, date_end)
        
        # Get timestamp column for summary
        timestamp_col = get_timestamp_column_info(list(merged_df.columns))
        
        # Add meteorological calculations (WBGT, etc.)
        merged_df = add_meteorological_calculations(merged_df)
        
        # Generate merge summary
        merge_summary = get_merge_summary(merged_df, timestamp_col, date_start, date_end)
        
        # Save outputs
        save_merged_data(merged_df, output_files)
        save_metadata(metadata_df, output_files['metadata'])
        
        # Create plots
        create_time_series_plots(merged_df, timestamp_col, output_files['plots'])
        create_summary_plot(merge_summary, output_files['plots'])
        
        # Validate plot output
        if not validate_plot_output(output_files['plots']):
            logger.warning("Plot file validation failed")
        
        # Print summary
        print_processing_summary(config, existing_files, missing_files, merge_summary, output_files)
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    # For direct execution
    from .cli import main
    main()
