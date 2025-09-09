# Tests for header parsing functionality

library(testthat)

test_that("Header parsing works correctly", {
  source("../R/parse_header.R")
  source("../R/utils.R")
  
  # Create test file
  test_content <- c(
    "TOA5,Biobasis_MM1,CR6,12345,CR6.Std.03.02,CPU:Biobasis.CR6,12345,Biobasis_MM1",
    "TIMESTAMP,RECORD,AirTC_Avg,RH_Avg",
    "TS,RN,Deg C,%",
    "Avg,Avg,Avg,Avg"
  )
  
  temp_file <- tempfile(fileext = ".dat")
  writeLines(test_content, temp_file)
  
  # Test parsing
  header_info <- parse_header(temp_file)
  
  expect_equal(header_info$columns, c("TIMESTAMP", "RECORD", "AirTC_Avg", "RH_Avg"))
  expect_equal(header_info$units[["AirTC_Avg"]], "Deg C")
  expect_equal(header_info$units[["RH_Avg"]], "%")
  expect_equal(header_info$stats[["TIMESTAMP"]], "Avg")
  
  unlink(temp_file)
})

test_that("Header parsing handles quoted values", {
  source("../R/parse_header.R")
  source("../R/utils.R")
  
  # Create test file with quoted values
  test_content <- c(
    "TOA5,Biobasis_MM1,CR6,12345,CR6.Std.03.02,CPU:Biobasis.CR6,12345,Biobasis_MM1",
    '"TIMESTAMP","RECORD","AirTC_Avg"',
    '"TS","RN","Deg C"',
    '"Avg","Avg","Avg"'
  )
  
  temp_file <- tempfile(fileext = ".dat")
  writeLines(test_content, temp_file)
  
  header_info <- parse_header(temp_file)
  
  expect_equal(header_info$columns, c("TIMESTAMP", "RECORD", "AirTC_Avg"))
  expect_equal(header_info$units[["AirTC_Avg"]], "Deg C")
  
  unlink(temp_file)
})

test_that("Header parsing handles insufficient lines", {
  source("../R/parse_header.R")
  source("../R/utils.R")
  
  # Create test file with insufficient lines
  test_content <- c(
    "TOA5,Biobasis_MM1,CR6,12345,CR6.Std.03.02,CPU:Biobasis.CR6,12345,Biobasis_MM1",
    "TIMESTAMP,RECORD"
  )
  
  temp_file <- tempfile(fileext = ".dat")
  writeLines(test_content, temp_file)
  
  expect_error(parse_header(temp_file), "fewer than 4 header lines")
  
  unlink(temp_file)
})

test_that("Timestamp column identification works", {
  source("../R/parse_header.R")
  source("../R/utils.R")
  
  # Test standard timestamp column
  expect_equal(get_timestamp_column_info(c("TIMESTAMP", "RECORD", "temp")), "TIMESTAMP")
  
  # Test lowercase timestamp
  expect_equal(get_timestamp_column_info(c("timestamp", "record", "temp")), "timestamp")
  
  # Test DateTime column
  expect_equal(get_timestamp_column_info(c("DateTime", "RECORD", "temp")), "DateTime")
  
  # Test no standard timestamp - should use first column
  expect_equal(get_timestamp_column_info(c("time_col", "RECORD", "temp")), "time_col")
  
  # Test empty columns
  expect_error(get_timestamp_column_info(character(0)), "No columns found")
})
