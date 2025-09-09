# Data merging and reindexing logic

library(dplyr)
library(lubridate)
source("parse_header.R")
source("utils.R")

concatenate_dataframes <- function(dataframes) {
  if (length(dataframes) == 0) {
    stop("No dataframes to concatenate")
  }
  
  merged_df <- bind_rows(dataframes)
  log_message("INFO", paste("Concatenated", length(dataframes), "dataframes into", nrow(merged_df), "rows"))
  
  return(merged_df)
}

sort_by_timestamp <- function(df, timestamp_col) {
  if (!(timestamp_col %in% names(df))) {
    stop(paste("Timestamp column", timestamp_col, "not found in dataframe"))
  }
  
  sorted_df <- df %>% arrange(!!sym(timestamp_col))
  log_message("DEBUG", paste("Sorted dataframe by", timestamp_col))
  
  return(sorted_df)
}

remove_duplicates <- function(df, timestamp_col) {
  initial_length <- nrow(df)
  
  # Remove duplicates based on timestamp column, keeping first occurrence
  deduped_df <- df %>% distinct(!!sym(timestamp_col), .keep_all = TRUE)
  
  duplicates_removed <- initial_length - nrow(deduped_df)
  if (duplicates_removed > 0) {
    log_message("WARNING", paste("Removed", duplicates_removed, "duplicate timestamps"))
  }
  
  return(deduped_df)
}

create_complete_time_index <- function(date_start, date_end, freq_mins = 30) {
  # Create start and end timestamps
  start_timestamp <- as.POSIXct(paste(date_start, "00:00:00"))
  end_timestamp <- as.POSIXct(paste(date_end, "23:30:00"))
  
  # Create complete time index
  complete_index <- seq(from = start_timestamp, to = end_timestamp, by = paste(freq_mins, "mins"))
  
  log_message("INFO", paste("Created complete time index with", length(complete_index), "timestamps"))
  return(complete_index)
}

reindex_to_complete_grid <- function(df, timestamp_col, date_start, date_end) {
  if (!(timestamp_col %in% names(df))) {
    stop(paste("Timestamp column", timestamp_col, "not found in dataframe"))
  }
  
  # Create complete time index
  complete_index <- create_complete_time_index(date_start, date_end)
  
  # Create complete grid dataframe
  complete_df <- data.frame(timestamp = complete_index)
  names(complete_df)[1] <- timestamp_col
  
  # Merge with existing data
  reindexed_df <- complete_df %>%
    left_join(df, by = timestamp_col)
  
  missing_count <- sum(is.na(reindexed_df[, !names(reindexed_df) %in% timestamp_col, drop = FALSE]))
  log_message("INFO", paste("Reindexed to complete grid:", nrow(reindexed_df), "timestamps,", missing_count, "missing values"))
  
  return(reindexed_df)
}

merge_daily_data <- function(dataframes, date_start, date_end) {
  if (length(dataframes) == 0) {
    stop("No dataframes provided for merging")
  }
  
  # Get timestamp column name from first dataframe
  timestamp_col <- get_timestamp_column_info(names(dataframes[[1]]))
  
  log_message("INFO", "Starting data merge pipeline")
  
  # Step 1: Concatenate
  merged_df <- concatenate_dataframes(dataframes)
  
  # Step 2: Sort by timestamp
  merged_df <- sort_by_timestamp(merged_df, timestamp_col)
  
  # Step 3: Remove duplicates
  merged_df <- remove_duplicates(merged_df, timestamp_col)
  
  # Step 4: Reindex to complete grid
  merged_df <- reindex_to_complete_grid(merged_df, timestamp_col, date_start, date_end)
  
  log_message("INFO", "Data merge pipeline completed successfully")
  return(merged_df)
}

get_merge_summary <- function(df, timestamp_col, date_start, date_end) {
  complete_index <- create_complete_time_index(date_start, date_end)
  expected_rows <- length(complete_index)
  actual_rows <- nrow(df)
  
  # Count missing timestamps (rows with all NA except timestamp)
  data_cols <- names(df)[names(df) != timestamp_col]
  missing_timestamps <- sum(apply(df[data_cols], 1, function(x) all(is.na(x))))
  
  data_coverage <- (actual_rows - missing_timestamps) / expected_rows * 100
  
  summary <- list(
    total_rows = actual_rows,
    expected_rows = expected_rows,
    missing_timestamps = missing_timestamps,
    data_coverage = data_coverage,
    timestamp_column = timestamp_col,
    date_range = paste(format(date_start, "%Y-%m-%d"), "to", format(date_end, "%Y-%m-%d"))
  )
  
  return(summary)
}
