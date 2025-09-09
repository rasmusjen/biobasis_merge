# Tests for CLI functionality

library(testthat)
library(yaml)

test_that("CLI option parsing works", {
  # Test that required arguments are validated
  # Note: In R, we can't easily test the full CLI without creating temporary scripts
  # So we test the underlying functions
  
  source("../R/cli.R")
  
  # Test option list creation
  options <- create_option_list()
  expect_length(options, 4)  # Should have 4 options
  expect_true(any(sapply(options, function(x) grepl("config", x$help))))
})

test_that("Configuration validation works", {
  source("../R/utils.R")
  
  # Test with missing config file
  expect_error(parse_config("/nonexistent/config.yaml"), "Configuration file not found")
  
  # Test with valid config
  temp_config <- tempfile(fileext = ".yaml")
  config_data <- list(
    input_dir = "/tmp/input",
    output_dir = "/tmp/output",
    date_start = "20240101",
    date_end = "20240102"
  )
  yaml::write_yaml(config_data, temp_config)
  
  config <- parse_config(temp_config)
  expect_equal(config$input_dir, "/tmp/input")
  expect_equal(config$date_start, "20240101")
  
  unlink(temp_config)
  
  # Test with missing required field
  temp_config2 <- tempfile(fileext = ".yaml")
  incomplete_config <- list(
    input_dir = "/tmp/input"
    # Missing required fields
  )
  yaml::write_yaml(incomplete_config, temp_config2)
  
  expect_error(parse_config(temp_config2), "Required field")
  
  unlink(temp_config2)
})
