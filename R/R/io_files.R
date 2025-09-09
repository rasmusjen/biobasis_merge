# File I/O operations for reading and discovering Biobasis data files

library(readr)
library(dplyr)
library(lubridate)
source("parse_header.R")
source("utils.R")

build_expected_file_list <- function(input_dir, date_start, date_end) {
  date_list <- generate_date_list(date_start, date_end)
  
  expected_files <- data.frame(
    date = date_list,
    file_path = file.path(input_dir, paste0("Biobasis_MM1_", format(date_list, "%Y%m%d"), ".dat")),
    stringsAsFactors = FALSE
  )
  
  return(expected_files)
}

check_file_existence <- function(file_list) {
  file_list$exists <- file.exists(file_list$file_path)
  
  existing <- file_list[file_list$exists, ]
  missing <- file_list[!file_list$exists, ]
  
  log_message("INFO", paste("Found", nrow(existing), "existing files,", nrow(missing), "missing files"))
  
  return(list(existing = existing, missing = missing))
}

read_data_file <- function(file_path) {
  tryCatch({
    # Parse header first
    header_info <- parse_header(file_path)
    
    # Read data starting from line 5
    df <- readr::read_csv(
      file_path,
      skip = 4,
      col_names = header_info$columns,
      show_col_types = FALSE
    )
    
    # Parse timestamp column
    timestamp_col <- get_timestamp_column_info(header_info$columns)
    
    if (timestamp_col %in% names(df)) {
      # Convert timestamp to POSIXct without timezone info
      df[[timestamp_col]] <- as.POSIXct(df[[timestamp_col]])
    }
    
    log_message("DEBUG", paste("Read", nrow(df), "rows from", file_path))
    
    return(list(
      data = df,
      units = header_info$units,
      stats = header_info$stats
    ))
    
  }, error = function(e) {
    log_message("ERROR", paste("Error reading file", file_path, ":", e$message))
    stop(e)
  })
}

load_all_files <- function(file_list) {
  dataframes <- list()
  units_list <- list()
  stats_list <- list()
  
  for (i in seq_len(nrow(file_list))) {
    file_path <- file_list$file_path[i]
    tryCatch({
      file_data <- read_data_file(file_path)
      dataframes[[length(dataframes) + 1]] <- file_data$data
      units_list[[length(units_list) + 1]] <- file_data$units
      stats_list[[length(stats_list) + 1]] <- file_data$stats
      log_message("DEBUG", paste("Successfully loaded", file_path))
    }, error = function(e) {
      log_message("WARNING", paste("Failed to load", file_path, ":", e$message))
    })
  }
  
  log_message("INFO", paste("Successfully loaded", length(dataframes), "files"))
  
  return(list(
    dataframes = dataframes,
    units_list = units_list,
    stats_list = stats_list
  ))
}

validate_output_paths <- function(output_dir, date_range, overwrite = FALSE) {
  base_name <- paste0("Biobasis_MM1_merged_", date_range)
  
  output_files <- list(
    csv = file.path(output_dir, paste0(base_name, ".csv")),
    metadata = file.path(output_dir, paste0(base_name, "_metadata.csv")),
    plots = file.path(output_dir, paste0(base_name, "_plots.html"))
  )
  
  # Check for existing files
  existing_files <- character(0)
  for (file_path in output_files) {
    if (file.exists(file_path)) {
      existing_files <- c(existing_files, file_path)
    }
  }
  
  if (length(existing_files) > 0 && !overwrite) {
    stop(paste("Output files already exist:", paste(existing_files, collapse = ", "), 
              ". Use --overwrite to overwrite existing files."))
  }
  
  return(output_files)
}
