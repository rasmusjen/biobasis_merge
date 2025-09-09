# Header parsing for Biobasis data files

source("utils.R")

parse_header <- function(file_path) {
  # Read first 4 lines
  lines <- readLines(file_path, n = 4)
  
  if (length(lines) < 4) {
    stop(paste("File", file_path, "has fewer than 4 header lines"))
  }
  
  # Line 2: Column names (split by comma, remove quotes)
  column_names <- trimws(gsub('"', '', strsplit(lines[2], ",")[[1]]))
  
  # Line 3: Units (split by comma, remove quotes)
  units_list <- trimws(gsub('"', '', strsplit(lines[3], ",")[[1]]))
  
  # Line 4: Statistics (split by comma, remove quotes)
  stats_list <- trimws(gsub('"', '', strsplit(lines[4], ",")[[1]]))
  
  # Create named vectors for units and stats
  units_dict <- setNames(rep("", length(column_names)), column_names)
  stats_dict <- setNames(rep("", length(column_names)), column_names)
  
  # Fill in available units and stats
  for (i in seq_along(column_names)) {
    if (i <= length(units_list)) {
      units_dict[column_names[i]] <- units_list[i]
    }
    if (i <= length(stats_list)) {
      stats_dict[column_names[i]] <- stats_list[i]
    }
  }
  
  log_message("DEBUG", paste("Parsed header from", file_path, ":", length(column_names), "columns"))
  
  return(list(
    columns = column_names,
    units = units_dict,
    stats = stats_dict
  ))
}

validate_header_consistency <- function(headers) {
  if (length(headers) == 0) {
    return()
  }
  
  reference_columns <- headers[[1]]$columns
  
  for (i in 2:length(headers)) {
    current_columns <- headers[[i]]$columns
    if (!identical(current_columns, reference_columns)) {
      log_message("WARNING", paste("Header", i, "has different columns than reference header"))
      
      ref_set <- reference_columns
      curr_set <- current_columns
      missing <- setdiff(ref_set, curr_set)
      extra <- setdiff(curr_set, ref_set)
      
      if (length(missing) > 0) {
        log_message("WARNING", paste("Missing columns:", paste(missing, collapse = ", ")))
      }
      if (length(extra) > 0) {
        log_message("WARNING", paste("Extra columns:", paste(extra, collapse = ", ")))
      }
    }
  }
}

get_timestamp_column_info <- function(column_names) {
  timestamp_candidates <- c('TIMESTAMP', 'timestamp', 'DateTime', 'datetime', 'TIME', 'time')
  
  for (candidate in timestamp_candidates) {
    if (candidate %in% column_names) {
      return(candidate)
    }
  }
  
  # If no standard timestamp column found, use first column
  if (length(column_names) > 0) {
    log_message("WARNING", paste("No standard timestamp column found, using first column:", column_names[1]))
    return(column_names[1])
  }
  
  stop("No columns found in header")
}
