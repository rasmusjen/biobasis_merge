# Utilities for configuration parsing, date handling, and logging setup

library(yaml)
library(lubridate)

setup_logging <- function(level = "INFO") {
  # R doesn't have built-in logging like Python, so we'll use simple print statements
  # In a production environment, you might want to use the 'logger' package
  options(biobasis.log.level = level)
  message(paste("Log level set to:", level))
}

log_message <- function(level, message) {
  current_level <- getOption("biobasis.log.level", "INFO")
  levels <- c("DEBUG" = 1, "INFO" = 2, "WARNING" = 3, "ERROR" = 4)
  
  if (levels[[level]] >= levels[[current_level]]) {
    timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
    cat(sprintf("%s - %s - %s\n", timestamp, level, message))
  }
}

parse_config <- function(config_path) {
  if (!file.exists(config_path)) {
    stop(paste("Configuration file not found:", config_path))
  }
  
  config <- yaml::read_yaml(config_path)
  
  # Validate required fields
  required_fields <- c('input_dir', 'output_dir', 'date_start', 'date_end')
  for (field in required_fields) {
    if (!(field %in% names(config))) {
      stop(paste("Required field", field, "missing from configuration"))
    }
  }
  
  return(config)
}

parse_date <- function(date_str) {
  # Try YYYYMMDD format first
  tryCatch({
    return(as.Date(date_str, format = "%Y%m%d"))
  }, error = function(e) {
    # Try YYYY-MM-DD format
    tryCatch({
      return(as.Date(date_str, format = "%Y-%m-%d"))
    }, error = function(e) {
      stop(paste("Invalid date format:", date_str, ". Use YYYYMMDD or YYYY-MM-DD"))
    })
  })
}

format_date_range <- function(date_start, date_end) {
  start_str <- format(date_start, "%Y%m%d")
  end_str <- format(date_end, "%Y%m%d")
  return(paste0(start_str, "-", end_str))
}

generate_date_list <- function(date_start, date_end) {
  return(seq(from = date_start, to = date_end, by = "day"))
}

validate_output_dir <- function(output_dir, create = TRUE) {
  if (create && !dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
  }
  return(output_dir)
}
