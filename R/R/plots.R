# Plot generation using Plotly for interactive HTML visualizations

library(plotly)
library(htmlwidgets)
library(dplyr)
source("utils.R")

determine_plot_columns <- function(df, exclude_columns = c('TIMESTAMP', 'RECORD', 'timestamp', 'record')) {
  plot_columns <- character(0)
  
  for (col in names(df)) {
    if (!(col %in% exclude_columns) && is.numeric(df[[col]])) {
      plot_columns <- c(plot_columns, col)
    }
  }
  
  log_message("DEBUG", paste("Selected", length(plot_columns), "columns for plotting"))
  return(plot_columns)
}

calculate_subplot_layout <- function(num_plots, max_cols = 2) {
  if (num_plots == 0) {
    return(list(rows = 1, cols = 1))
  }
  
  cols <- min(num_plots, max_cols)
  rows <- ceiling(num_plots / cols)
  
  return(list(rows = rows, cols = cols))
}

downsample_data <- function(df, max_points = 200000) {
  if (nrow(df) <= max_points) {
    return(df)
  }
  
  # Calculate stride for downsampling
  stride <- ceiling(nrow(df) / max_points)
  indices <- seq(1, nrow(df), by = stride)
  downsampled <- df[indices, ]
  
  log_message("INFO", paste("Downsampled data from", nrow(df), "to", nrow(downsampled), "points (stride =", stride, ")"))
  return(downsampled)
}

create_time_series_plots <- function(df, timestamp_col, output_path) {
  tryCatch({
    # Determine columns to plot
    all_plot_columns <- determine_plot_columns(df)
    
    if (length(all_plot_columns) == 0) {
      log_message("WARNING", "No numeric columns found for plotting")
      
      # Create empty plot
      p <- plot_ly() %>%
        add_annotations(
          text = "No numeric data columns available for plotting",
          x = 0.5, y = 0.5,
          xref = "paper", yref = "paper",
          showarrow = FALSE,
          font = list(size = 16)
        ) %>%
        layout(title = "Biobasis Meteorological Data - No Data")
      
      htmlwidgets::saveWidget(p, output_path, selfcontained = FALSE)
      return()
    }
    
    # Downsample if necessary
    plot_df <- downsample_data(df)
    
    # Special handling for temperature plots
    temp_columns <- c('BGTemp_C_Avg', 'AirTC_Avg')
    has_temp_data <- any(temp_columns %in% all_plot_columns)
    
    # Create plot structure
    plot_columns <- character(0)
    subplot_titles <- character(0)
    
    if (has_temp_data) {
      # Add combined temperature plot
      plot_columns <- c(plot_columns, 'Temperature')
      subplot_titles <- c(subplot_titles, 'Temperature (°C)')
      
      # Add other columns (excluding temperature columns)
      other_columns <- all_plot_columns[!all_plot_columns %in% temp_columns]
      plot_columns <- c(plot_columns, other_columns)
      subplot_titles <- c(subplot_titles, other_columns)
    } else {
      plot_columns <- all_plot_columns
      subplot_titles <- all_plot_columns
    }
    
    # Calculate subplot layout
    layout <- calculate_subplot_layout(length(plot_columns))
    
    plots <- list()
    for (i in seq_along(plot_columns)) {
      column <- plot_columns[i]
      
      if (column == 'Temperature' && has_temp_data) {
        # Special handling for combined temperature plot
        temp_plot <- plot_ly()
        colors <- c('red', 'blue')
        
        for (j in seq_along(temp_columns)) {
          temp_col <- temp_columns[j]
          if (temp_col %in% names(plot_df) && !all(is.na(plot_df[[temp_col]]))) {
            temp_plot <- temp_plot %>%
              add_lines(
                data = plot_df,
                x = plot_df[[timestamp_col]], 
                y = plot_df[[temp_col]],
                name = temp_col,
                line = list(color = colors[j]),
                showlegend = TRUE
              )
          }
        }
        
        plots[[i]] <- temp_plot %>%
          layout(
            xaxis = list(title = "Time (UTC)"),
            yaxis = list(title = "Temperature (°C)")
          )
      } else {
        # Regular single column plot
        if (column %in% names(plot_df)) {
          # Skip columns with all NA values
          if (all(is.na(plot_df[[column]]))) {
            log_message("DEBUG", paste("Skipping column", column, "- all NA values"))
            plots[[i]] <- plot_ly() %>%
              add_annotations(
                text = paste("No data for", column),
                x = 0.5, y = 0.5,
                showarrow = FALSE
              )
            next
          }
          
          plots[[i]] <- plot_ly(data = plot_df, x = plot_df[[timestamp_col]], y = plot_df[[column]]) %>%
            add_lines(name = column, showlegend = FALSE) %>%
            layout(
              xaxis = list(title = "Time (UTC)"),
              yaxis = list(title = column)
            )
        }
      }
    }
    
    # Combine subplots
    if (length(plots) == 1) {
      final_plot <- plots[[1]]
    } else {
      final_plot <- subplot(plots, nrows = layout$rows, shareX = TRUE, titleY = TRUE) %>%
        layout(
          title = list(
            text = "Biobasis Meteorological Data Time Series",
            x = 0.5,
            font = list(size = 16)
          ),
          showlegend = has_temp_data  # Only show legend for temperature plot
        )
    }
    
    # Save to HTML
    htmlwidgets::saveWidget(final_plot, output_path, selfcontained = FALSE)
    
    effective_plots <- if (!has_temp_data) length(all_plot_columns) else length(all_plot_columns) - 1
    log_message("INFO", paste("Created interactive plots with", effective_plots, "variables, saved to", output_path))
    
  }, error = function(e) {
    log_message("ERROR", paste("Failed to create plots:", e$message))
    stop(e)
  })
}

create_summary_plot <- function(merge_summary, output_path) {
  tryCatch({
    coverage <- merge_summary$data_coverage
    missing_pct <- 100 - coverage
    
    p <- plot_ly(
      x = c('Data Coverage', 'Missing Data'),
      y = c(coverage, missing_pct),
      type = 'bar',
      marker = list(color = c('green', 'red')),
      text = paste0(c(coverage, missing_pct), "%"),
      textposition = 'auto'
    ) %>%
      layout(
        title = paste0("Data Coverage Summary<br>", merge_summary$date_range),
        yaxis = list(title = "Percentage"),
        showlegend = FALSE
      ) %>%
      add_annotations(
        text = paste0(
          "Total rows: ", merge_summary$total_rows, "<br>",
          "Expected rows: ", merge_summary$expected_rows, "<br>",
          "Missing timestamps: ", merge_summary$missing_timestamps
        ),
        x = 0.02, y = 0.98,
        xref = "paper", yref = "paper",
        showarrow = FALSE,
        align = "left",
        bgcolor = "lightgray",
        bordercolor = "black",
        borderwidth = 1
      )
    
    # Save summary plot separately
    summary_path <- gsub('\\.html$', '_summary.html', output_path)
    htmlwidgets::saveWidget(p, summary_path, selfcontained = FALSE)
    
    log_message("INFO", paste("Created summary plot:", summary_path))
    
  }, error = function(e) {
    log_message("WARNING", paste("Failed to create summary plot:", e$message))
  })
}

validate_plot_output <- function(output_path) {
  if (!file.exists(output_path)) {
    return(FALSE)
  }
  
  # Check file size (should be > 0)
  if (file.info(output_path)$size == 0) {
    return(FALSE)
  }
  
  # Basic content check (should contain plotly)
  tryCatch({
    content <- readLines(output_path, n = 50)  # Read first 50 lines
    if (!any(grepl("plotly", content, ignore.case = TRUE))) {
      return(FALSE)
    }
  }, error = function(e) {
    return(FALSE)
  })
  
  return(TRUE)
}
