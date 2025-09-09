# Command-line interface for R implementation

library(optparse)

source("utils.R")
source("main.R")

create_option_list <- function() {
  option_list <- list(
    make_option(c("--config"), type = "character", default = NULL,
                help = "Path to YAML configuration file", metavar = "character"),
    make_option(c("--dry-run"), action = "store_true", default = FALSE,
                help = "Show what would be processed without actually running"),
    make_option(c("--overwrite"), action = "store_true", default = FALSE,
                help = "Overwrite existing output files"),
    make_option(c("--log-level"), type = "character", default = "INFO",
                help = "Set logging level [default= %default]", metavar = "character")
  )
  return(option_list)
}

parse_arguments <- function() {
  option_list <- create_option_list()
  
  opt_parser <- OptionParser(
    option_list = option_list,
    description = "Merge daily Biobasis meteorological data files"
  )
  
  opt <- parse_args(opt_parser)
  
  if (is.null(opt$config)) {
    print_help(opt_parser)
    stop("--config argument is required", call. = FALSE)
  }
  
  return(opt)
}

main <- function() {
  args <- parse_arguments()
  
  tryCatch({
    main_pipeline(
      config_path = args$config,
      dry_run = args$`dry-run`,
      overwrite = args$overwrite,
      log_level = args$`log-level`
    )
  }, error = function(e) {
    cat("Error:", e$message, "\n", file = stderr())
    quit(status = 1)
  })
}

# Run if script is executed directly
if (!interactive()) {
  main()
}
