# Tests for merge logic functionality

library(testthat)
library(dplyr)
library(lubridate)

test_that("Dataframe concatenation works", {
  source("../R/merge_logic.R")
  source("../R/utils.R")
  
  df1 <- data.frame(
    TIMESTAMP = as.POSIXct(c("2024-01-01 00:00:00", "2024-01-01 00:30:00"), tz = "UTC"),
    value = c(1, 2)
  )
  
  df2 <- data.frame(
    TIMESTAMP = as.POSIXct(c("2024-01-01 01:00:00", "2024-01-01 01:30:00"), tz = "UTC"),
    value = c(3, 4)
  )
  
  result <- concatenate_dataframes(list(df1, df2))
  
  expect_equal(nrow(result), 4)
  expect_equal(result$value, c(1, 2, 3, 4))
})

test_that("Concatenation fails with empty list", {
  source("../R/merge_logic.R")
  source("../R/utils.R")
  
  expect_error(concatenate_dataframes(list()), "No dataframes to concatenate")
})

test_that("Sorting by timestamp works", {
  source("../R/merge_logic.R")
  source("../R/parse_header.R")
  source("../R/utils.R")
  
  # Create unsorted dataframe
  df <- data.frame(
    TIMESTAMP = as.POSIXct(c("2024-01-01 01:00:00", "2024-01-01 00:00:00", "2024-01-01 00:30:00"), tz = "UTC"),
    value = c(2, 1, 3)
  )
  
  result <- sort_by_timestamp(df, "TIMESTAMP")
  
  expect_equal(result$value, c(1, 3, 2))  # Values sorted by timestamp
})

test_that("Duplicate removal works", {
  source("../R/merge_logic.R")
  source("../R/utils.R")
  
  # Create dataframe with duplicate timestamps
  df <- data.frame(
    TIMESTAMP = as.POSIXct(c("2024-01-01 00:00:00", "2024-01-01 00:00:00", "2024-01-01 00:30:00"), tz = "UTC"),
    value = c(1, 2, 3)  # First occurrence should be kept
  )
  
  result <- remove_duplicates(df, "TIMESTAMP")
  
  expect_equal(nrow(result), 2)
  expect_equal(result$value, c(1, 3))  # First occurrence kept
})

test_that("Complete time index creation works", {
  source("../R/merge_logic.R")
  source("../R/utils.R")
  
  date_start <- as.Date("2024-01-01")
  date_end <- as.Date("2024-01-01")  # Same day
  
  index <- create_complete_time_index(date_start, date_end)
  
  # Should have 48 timestamps for one day (00:00 to 23:30 at 30-min intervals)
  expect_equal(length(index), 48)
  expect_equal(as.character(index[1]), "2024-01-01 00:00:00 UTC")
  expect_equal(as.character(index[48]), "2024-01-01 23:30:00 UTC")
})

test_that("Reindexing to complete grid works", {
  source("../R/merge_logic.R")
  source("../R/utils.R")
  
  # Create sparse dataframe
  df <- data.frame(
    TIMESTAMP = as.POSIXct(c("2024-01-01 00:00:00", "2024-01-01 01:00:00"), tz = "UTC"),  # Missing 00:30
    value = c(1, 2)
  )
  
  date_start <- as.Date("2024-01-01")
  date_end <- as.Date("2024-01-01")
  
  result <- reindex_to_complete_grid(df, "TIMESTAMP", date_start, date_end)
  
  # Should have 48 rows for complete day
  expect_equal(nrow(result), 48)
  
  # Check that missing values are NA
  expect_true(is.na(result$value[2]))  # 00:30 should be NA
  expect_equal(result$value[1], 1)     # 00:00 should be 1
  expect_equal(result$value[3], 2)     # 01:00 should be 2
})

test_that("Complete merge pipeline works", {
  source("../R/merge_logic.R")
  source("../R/parse_header.R")
  source("../R/utils.R")
  
  # Create two dataframes with some overlap and gaps
  df1 <- data.frame(
    TIMESTAMP = as.POSIXct(c("2024-01-01 00:00:00", "2024-01-01 00:30:00", "2024-01-01 01:00:00"), tz = "UTC"),
    value = c(1, 2, 3)
  )
  
  df2 <- data.frame(
    TIMESTAMP = as.POSIXct(c("2024-01-01 01:00:00", "2024-01-01 01:30:00"), tz = "UTC"),  # 01:00 is duplicate
    value = c(4, 5)  # 4 should be ignored (duplicate), 5 should be kept
  )
  
  date_start <- as.Date("2024-01-01")
  date_end <- as.Date("2024-01-01")
  
  result <- merge_daily_data(list(df1, df2), date_start, date_end)
  
  # Should have complete day (48 timestamps)
  expect_equal(nrow(result), 48)
  
  # Check specific values
  expect_equal(result$value[1], 1)    # 00:00
  expect_equal(result$value[2], 2)    # 00:30
  expect_equal(result$value[3], 3)    # 01:00 (first occurrence)
  expect_equal(result$value[4], 5)    # 01:30
})
