# Metadata consolidation across multiple files

library(dplyr)
source("utils.R")

consolidate_metadata <- function(units_list, stats_list) {
  if (length(units_list) == 0 || length(stats_list) == 0) {
    return(list(units = character(0), stats = character(0)))
  }
  
  # Get all unique column names
  all_columns <- unique(unlist(lapply(units_list, names)))
  
  consolidated_units <- setNames(rep("", length(all_columns)), all_columns)
  consolidated_stats <- setNames(rep("", length(all_columns)), all_columns)
  
  # For each column, find first non-empty unit and stat
  for (column in all_columns) {
    # Consolidate units
    for (units_dict in units_list) {
      if (column %in% names(units_dict) && 
          !is.na(units_dict[[column]]) && 
          nchar(trimws(units_dict[[column]])) > 0) {
        consolidated_units[[column]] <- trimws(units_dict[[column]])
        break
      }
    }
    
    # Consolidate stats
    for (stats_dict in stats_list) {
      if (column %in% names(stats_dict) && 
          !is.na(stats_dict[[column]]) && 
          nchar(trimws(stats_dict[[column]])) > 0) {
        consolidated_stats[[column]] <- trimws(stats_dict[[column]])
        break
      }
    }
  }
  
  log_message("INFO", paste("Consolidated metadata for", length(all_columns), "columns"))
  
  return(list(
    units = consolidated_units,
    stats = consolidated_stats
  ))
}

create_metadata_dataframe <- function(units_dict, stats_dict) {
  # Get all columns
  all_columns <- unique(c(names(units_dict), names(stats_dict)))
  
  metadata_df <- data.frame(
    column_name = all_columns,
    unit = sapply(all_columns, function(col) ifelse(col %in% names(units_dict), units_dict[[col]], "")),
    statistic = sapply(all_columns, function(col) ifelse(col %in% names(stats_dict), stats_dict[[col]], "")),
    stringsAsFactors = FALSE
  )
  
  # Sort by column name
  metadata_df <- metadata_df %>% arrange(column_name)
  
  log_message("DEBUG", paste("Created metadata dataframe with", nrow(metadata_df), "rows"))
  
  return(metadata_df)
}

validate_metadata_consistency <- function(units_list, stats_list) {
  if (length(units_list) != length(stats_list)) {
    log_message("WARNING", paste("Mismatch in metadata list lengths:", length(units_list), "units vs", length(stats_list), "stats"))
  }
  
  if (length(units_list) <= 1) {
    return() # No comparison possible
  }
  
  # Check for inconsistent units
  all_columns <- unique(unlist(lapply(units_list, names)))
  
  for (column in all_columns) {
    unique_units <- character(0)
    for (units_dict in units_list) {
      if (column %in% names(units_dict) && 
          !is.na(units_dict[[column]]) && 
          nchar(trimws(units_dict[[column]])) > 0) {
        unique_units <- c(unique_units, trimws(units_dict[[column]]))
      }
    }
    
    if (length(unique(unique_units)) > 1) {
      log_message("WARNING", paste("Column", column, "has inconsistent units across files:", paste(unique(unique_units), collapse = ", ")))
    }
  }
  
  # Check for inconsistent stats
  for (column in all_columns) {
    unique_stats <- character(0)
    for (stats_dict in stats_list) {
      if (column %in% names(stats_dict) && 
          !is.na(stats_dict[[column]]) && 
          nchar(trimws(stats_dict[[column]])) > 0) {
        unique_stats <- c(unique_stats, trimws(stats_dict[[column]]))
      }
    }
    
    if (length(unique(unique_stats)) > 1) {
      log_message("WARNING", paste("Column", column, "has inconsistent statistics across files:", paste(unique(unique_stats), collapse = ", ")))
    }
  }
}

save_metadata <- function(metadata_df, output_path) {
  tryCatch({
    write.csv(metadata_df, output_path, row.names = FALSE)
    log_message("INFO", paste("Saved metadata to", output_path))
  }, error = function(e) {
    log_message("ERROR", paste("Failed to save metadata to", output_path, ":", e$message))
    stop(e)
  })
}
