# Tests for plot generation functionality

library(testthat)
library(plotly)

test_that("Plot column determination works", {
  source("../R/plots.R")
  source("../R/utils.R")
  
  df <- data.frame(
    TIMESTAMP = seq(as.POSIXct("2024-01-01"), length.out = 10, by = "30 mins"),
    RECORD = 1:10,
    temperature = runif(10, 20, 25),
    humidity = runif(10, 60, 70),
    text_col = letters[1:10],
    stringsAsFactors = FALSE
  )
  
  plot_columns <- determine_plot_columns(df)
  
  # Should exclude TIMESTAMP, RECORD, and text columns
  expected <- c("temperature", "humidity")
  expect_equal(sort(plot_columns), sort(expected))
})

test_that("Subplot layout calculation works", {
  source("../R/plots.R")
  source("../R/utils.R")
  
  # Test various numbers of plots
  expect_equal(calculate_subplot_layout(0), list(rows = 1, cols = 1))
  expect_equal(calculate_subplot_layout(1), list(rows = 1, cols = 1))
  expect_equal(calculate_subplot_layout(2), list(rows = 1, cols = 2))
  expect_equal(calculate_subplot_layout(3), list(rows = 2, cols = 2))
  expect_equal(calculate_subplot_layout(4), list(rows = 2, cols = 2))
  expect_equal(calculate_subplot_layout(5), list(rows = 3, cols = 2))
})

test_that("Data downsampling works", {
  source("../R/plots.R")
  source("../R/utils.R")
  
  # Create large dataframe
  df <- data.frame(
    time = seq(as.POSIXct("2024-01-01"), length.out = 1000, by = "1 min"),
    value = 1:1000
  )
  
  # Test no downsampling needed
  result <- downsample_data(df, max_points = 2000)
  expect_equal(nrow(result), 1000)
  
  # Test downsampling
  result <- downsample_data(df, max_points = 100)
  expect_lte(nrow(result), 100)
  expect_gt(nrow(result), 0)
})

test_that("Plot creation works with valid data", {
  source("../R/plots.R")
  source("../R/utils.R")
  
  # Create test dataframe
  df <- data.frame(
    TIMESTAMP = seq(as.POSIXct("2024-01-01", tz = "UTC"), length.out = 48, by = "30 mins"),
    RECORD = 1:48,
    temperature = 20 + (1:48) * 0.1,
    humidity = 65 + (1:48) * 0.2
  )
  
  temp_file <- tempfile(fileext = ".html")
  
  # This should not error
  expect_error(create_time_series_plots(df, "TIMESTAMP", temp_file), NA)
  
  # Check that file was created
  expect_true(file.exists(temp_file))
  expect_gt(file.info(temp_file)$size, 0)
  
  unlink(temp_file)
})

test_that("Plot validation works", {
  source("../R/plots.R")
  source("../R/utils.R")
  
  # Test non-existent file
  expect_false(validate_plot_output("/nonexistent/file.html"))
  
  # Test empty file
  temp_empty <- tempfile(fileext = ".html")
  file.create(temp_empty)
  expect_false(validate_plot_output(temp_empty))
  unlink(temp_empty)
  
  # Test valid HTML file with plotly content
  temp_valid <- tempfile(fileext = ".html")
  writeLines('<html><head><script src="plotly.js"></script></head></html>', temp_valid)
  expect_true(validate_plot_output(temp_valid))
  unlink(temp_valid)
  
  # Test invalid HTML file without plotly
  temp_invalid <- tempfile(fileext = ".html")
  writeLines('<html><head></head><body>No plotly here</body></html>', temp_invalid)
  expect_false(validate_plot_output(temp_invalid))
  unlink(temp_invalid)
})
