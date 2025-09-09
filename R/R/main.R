# Main orchestration pipeline for R implementation

library(arrow)
library(readr)
source("utils.R")
source("io_files.R")
source("merge_logic.R")
source("metadata.R")
source("plots.R")
source("parse_header.R")
source("meteorology.R")

save_merged_data <- function(df, output_files) {
  tryCatch({
    # Prepare dataframe for output
    output_df <- df
    
    # Format timestamp column to simple format (no timezone)
    timestamp_cols <- names(output_df)[grepl("TIMESTAMP", toupper(names(output_df)))]
    for (col in timestamp_cols) {
      if (inherits(output_df[[col]], "POSIXct")) {
        output_df[[col]] <- format(output_df[[col]], "%Y-%m-%d %H:%M:%S")
      }
    }
    
    # Save as uncompressed CSV with explicit NA handling
    readr::write_csv(output_df, output_files$csv, na = "NaN")
    log_message("INFO", paste("Saved CSV file:", output_files$csv))
    
  }, error = function(e) {
    log_message("ERROR", paste("Failed to save merged data:", e$message))
    stop(e)
  })
}

print_processing_summary <- function(config, file_status, merge_summary, output_files) {
  cat("\n", paste(rep("=", 60), collapse = ""), "\n")
  cat("BIOBASIS MERGE PROCESSING SUMMARY\n")
  cat(paste(rep("=", 60), collapse = ""), "\n")
  
  cat("\nConfiguration:\n")
  cat("  Input directory:", config$input_dir, "\n")
  cat("  Output directory:", config$output_dir, "\n")
  cat("  Date range:", config$date_start, "to", config$date_end, "\n")
  
  cat("\nFile Discovery:\n")
  cat("  Expected files:", nrow(file_status$existing) + nrow(file_status$missing), "\n")
  cat("  Found files:", nrow(file_status$existing), "\n")
  cat("  Missing files:", nrow(file_status$missing), "\n")
  
  if (nrow(file_status$missing) > 0) {
    missing_dates <- format(file_status$missing$date[1:min(5, nrow(file_status$missing))], "%Y%m%d")
    cat("  Missing file dates:", paste(missing_dates, collapse = ", "), "\n")
    if (nrow(file_status$missing) > 5) {
      cat("    ... and", nrow(file_status$missing) - 5, "more\n")
    }
  }
  
  cat("\nData Processing:\n")
  cat("  Total rows:", format(merge_summary$total_rows, big.mark = ","), "\n")
  cat("  Expected rows:", format(merge_summary$expected_rows, big.mark = ","), "\n")
  cat("  Missing timestamps:", format(merge_summary$missing_timestamps, big.mark = ","), "\n")
  cat("  Data coverage:", sprintf("%.1f%%", merge_summary$data_coverage), "\n")
  cat("  Timestamp column:", merge_summary$timestamp_column, "\n")
  
  cat("\nOutput Files:\n")
  for (file_type in names(output_files)) {
    file_path <- output_files[[file_type]]
    file_exists <- file.exists(file_path)
    status <- ifelse(file_exists, "✓", "✗")
    cat("  ", status, " ", toupper(file_type), ": ", file_path, "\n")
  }
  
  cat("\n", paste(rep("=", 60), collapse = ""), "\n")
}

main_pipeline <- function(config_path, dry_run = FALSE, overwrite = FALSE, log_level = "INFO") {
  # Setup logging
  setup_logging(log_level)
  log_message("INFO", "Starting Biobasis merge pipeline")
  
  tryCatch({
    # Load configuration
    config <- parse_config(config_path)
    log_message("INFO", paste("Loaded configuration from", config_path))
    
    # Parse dates
    date_start <- parse_date(config$date_start)
    date_end <- parse_date(config$date_end)
    date_range <- format_date_range(date_start, date_end)
    
    log_message("INFO", paste("Processing date range:", format(date_start, "%Y-%m-%d"), "to", format(date_end, "%Y-%m-%d")))
    
    # Validate and create output directory
    output_dir <- validate_output_dir(config$output_dir, create = !dry_run)
    
    # Validate output file paths
    output_files <- validate_output_paths(config$output_dir, date_range, overwrite)
    
    # Build expected file list
    expected_files <- build_expected_file_list(config$input_dir, date_start, date_end)
    
    # Check file existence
    file_status <- check_file_existence(expected_files)
    
    if (nrow(file_status$existing) == 0) {
      stop("No input files found in the specified date range")
    }
    
    if (dry_run) {
      cat("\nDRY RUN - Would process", nrow(file_status$existing), "files\n")
      cat("Missing", nrow(file_status$missing), "files\n")
      cat("Output files would be created in:", config$output_dir, "\n")
      return()
    }
    
    # Load all data files
    file_data <- load_all_files(file_status$existing)
    
    if (length(file_data$dataframes) == 0) {
      stop("Failed to load any data files")
    }
    
    # Validate metadata consistency
    validate_metadata_consistency(file_data$units_list, file_data$stats_list)
    
    # Consolidate metadata
    consolidated_metadata <- consolidate_metadata(file_data$units_list, file_data$stats_list)
    metadata_df <- create_metadata_dataframe(consolidated_metadata$units, consolidated_metadata$stats)
    
    # Merge data
    merged_df <- merge_daily_data(file_data$dataframes, date_start, date_end)
    
    # Get timestamp column for summary
    timestamp_col <- get_timestamp_column_info(names(merged_df))
    
    # Add meteorological calculations (WBGT, etc.)
    merged_df <- add_meteorological_calculations(merged_df)
    
    # Generate merge summary
    merge_summary <- get_merge_summary(merged_df, timestamp_col, date_start, date_end)
    
    # Save outputs
    save_merged_data(merged_df, output_files)
    save_metadata(metadata_df, output_files$metadata)
    
    # Create plots
    create_time_series_plots(merged_df, timestamp_col, output_files$plots)
    create_summary_plot(merge_summary, output_files$plots)
    
    # Validate plot output
    if (!validate_plot_output(output_files$plots)) {
      log_message("WARNING", "Plot file validation failed")
    }
    
    # Print summary
    print_processing_summary(config, file_status, merge_summary, output_files)
    
    log_message("INFO", "Pipeline completed successfully")
    
  }, error = function(e) {
    log_message("ERROR", paste("Pipeline failed:", e$message))
    stop(e)
  })
}
