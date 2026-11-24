#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 4L || length(args) > 5L) {
  stop(
    "Usage: compare_gdsc2_target_drugs_all_cell_lines_gdscic50.R ",
    "<normalized_wells.csv> <GDSC2_fitted_dose_response_24Jul22.csv> ",
    "<comparison_output.csv> <diagnostic_output.csv> [true|false]"
  )
}
is_large_data <- if (length(args) == 5L) tolower(args[[5]]) else "true"
if (!is_large_data %in% c("true", "false")) {
  stop("The optional model mode must be either true or false.")
}
is_large_data <- is_large_data == "true"
if (file.exists(args[[3]]) || file.exists(args[[4]])) {
  stop("Output already exists; choose new output paths.")
}
if (!requireNamespace("gdscIC50", quietly = TRUE)) {
  stop("Install the official CancerRxGene/gdscIC50 package before running.")
}
if (as.character(utils::packageVersion("gdscIC50")) != "0.99.4") {
  stop("This comparison was checked with gdscIC50 version 0.99.4.")
}
library(gdscIC50)

wells <- utils::read.csv(args[[1]], stringsAsFactors = FALSE)
reference <- utils::read.csv(args[[2]], stringsAsFactors = FALSE)
required_wells <- c(
  "scan_id", "cosmic_id", "cell_line", "drug_id", "drug_name",
  "drugset_id", "library_tag", "concentration_uM", "viability_fraction"
)
required_reference <- c(
  "DATASET", "COSMIC_ID", "CELL_LINE_NAME", "DRUG_ID", "DRUG_NAME",
  "MAX_CONC", "LN_IC50", "AUC", "RMSE"
)
if (!all(required_wells %in% names(wells))) {
  stop("Normalized-wells CSV is missing required extractor columns.")
}
if (!all(required_reference %in% names(reference))) {
  stop("Fitted-dose-response CSV is missing required GDSC2 columns.")
}

target_drugs <- c("1005", "1017", "1073", "1080", "1190")
wells$drug_id <- as.character(wells$drug_id)
wells$cosmic_id <- as.numeric(wells$cosmic_id)
reference <- reference[
  reference$DATASET == "GDSC2" &
    as.character(reference$DRUG_ID) %in% target_drugs,
  ,
  drop = FALSE
]
reference$DRUG_ID <- as.character(reference$DRUG_ID)
if (anyDuplicated(paste(reference$COSMIC_ID, reference$DRUG_ID, sep = "_"))) {
  stop("Official reference contains duplicate cell-line/drug rows.")
}
if (any(!is.finite(reference$MAX_CONC)) ||
    any(reference$MAX_CONC <= 0) ||
    any(!is.finite(reference$LN_IC50))) {
  stop("Official reference has invalid concentrations or LN_IC50 values.")
}
if (any(!is.finite(wells$concentration_uM)) ||
    any(wells$concentration_uM <= 0) ||
    any(!is.finite(wells$viability_fraction)) ||
    any(wells$viability_fraction < 0 | wells$viability_fraction > 1)) {
  stop("Normalized wells have invalid dose or viability values.")
}

reference$key <- paste(reference$COSMIC_ID, reference$DRUG_ID, sep = "_")
wells$key <- paste(wells$cosmic_id, wells$drug_id, sep = "_")
raw_only_keys <- setdiff(unique(wells$key), reference$key)
wells <- wells[wells$key %in% reference$key, , drop = FALSE]
if (nrow(wells) == 0L) {
  stop("No normalized wells overlap the official fitted reference.")
}
if (anyDuplicated(reference$key)) {
  stop("Official reference key must be unique.")
}
reference_index <- match(wells$key, reference$key)
wells$maxc <- reference$MAX_CONC[reference_index]
wells$x <- log2(wells$concentration_uM / wells$maxc) + 9
wells$y <- 1 - wells$viability_fraction
wells$CL <- as.character(wells$cosmic_id)
wells$drug <- paste(
  wells$drug_id,
  format(wells$maxc, digits = 15, scientific = FALSE, trim = TRUE),
  sep = "_"
)
if (any(!is.finite(wells$x)) || any(wells$x > 9 + 1e-10)) {
  stop("Dose conversion produced invalid values or exceeds official maxc.")
}

observed_max <- tapply(
  wells$concentration_uM, wells$drug_id, max, na.rm = TRUE
)
reference_max <- tapply(reference$MAX_CONC, reference$DRUG_ID, unique)
if (!setequal(names(observed_max), names(reference_max)) ||
    any(vapply(names(observed_max), function(drug_id) {
      length(reference_max[[drug_id]]) != 1L ||
        !isTRUE(all.equal(
          unname(observed_max[[drug_id]]),
          reference_max[[drug_id]][[1]],
          tolerance = 1e-10
        ))
    }, logical(1)))) {
  stop("Observed maximum doses do not match the official fitted reference.")
}

model_well_data <- wells[c("CL", "x", "y", "drug", "maxc")]
maxc_by_drug <- unique(model_well_data[c("drug", "maxc")])
if (anyDuplicated(maxc_by_drug$drug)) {
  stop("Each model drug group must map to exactly one maximum concentration.")
}
model_data <- stats::aggregate(
  y ~ CL + x + drug,
  data = model_well_data,
  FUN = mean
)
model_data <- merge(model_data, maxc_by_drug, by = "drug", sort = FALSE)
if (any(!is.finite(model_data$x)) || any(!is.finite(model_data$y)) ||
    any(!is.finite(model_data$maxc))) {
  stop("Curve averaging produced invalid NLME model input.")
}
diagnostic <- data.frame(
  gdscIC50_version = as.character(utils::packageVersion("gdscIC50")),
  model_structure = paste0("official isLargeData=", is_large_data),
  target_drug_count = length(target_drugs),
  official_reference_combinations = nrow(reference),
  raw_only_combinations_excluded = length(raw_only_keys),
  normalized_wells_before_curve_averaging = nrow(model_well_data),
  model_observation_count_after_curve_averaging = nrow(model_data),
  cell_line_count = length(unique(model_data$CL)),
  drug_group_count = length(unique(model_data$drug)),
  scan_count = length(unique(wells$scan_id)),
  fit_status = "RUNNING",
  iterations = NA_integer_,
  covariance_positive_definite = NA,
  fit_error = "",
  fit_warnings = "",
  comparison_rows = NA_integer_,
  pearson_correlation = NA_real_,
  mean_signed_difference_ln = NA_real_,
  median_absolute_difference_ln = NA_real_,
  max_absolute_difference_ln = NA_real_,
  scan_drug_curve_count = NA_integer_,
  scan_drug_curve_crossings_50_percent = NA_integer_,
  combinations_with_any_scan_crossing = NA_integer_,
  combinations_without_scan_crossing = NA_integer_,
  median_absolute_difference_ln_with_crossing = NA_real_,
  median_absolute_difference_ln_without_crossing = NA_real_,
  mean_signed_difference_ln_with_crossing = NA_real_,
  mean_signed_difference_ln_without_crossing = NA_real_,
  stringsAsFactors = FALSE
)
utils::write.csv(diagnostic, args[[4]], row.names = FALSE)
cat(
  "Starting official NLME fit with", nrow(model_data),
  "mean dose-response observations from", nrow(model_well_data), "wells,",
  length(unique(model_data$CL)), "cell lines and",
  length(unique(model_data$drug)), "drug groups.\n"
)
flush.console()
fit_warnings <- character()
fit_error <- ""
model <- tryCatch(
  withCallingHandlers(
    gdscIC50::fitModelNlmeData(model_data, isLargeData = is_large_data),
    warning = function(warning) {
      fit_warnings <<- c(fit_warnings, conditionMessage(warning))
      invokeRestart("muffleWarning")
    }
  ),
  error = function(error) {
    fit_error <<- conditionMessage(error)
    NULL
  }
)

covariance_ok <- !is.null(model) && is.matrix(model$apVar) &&
  all(is.finite(model$apVar)) &&
  !inherits(try(chol(model$apVar), silent = TRUE), "try-error")
converged <- !is.null(model) &&
  model$numIter < 50L &&
  covariance_ok &&
  !nzchar(fit_error) &&
  length(fit_warnings) == 0L

diagnostic$fit_status <- if (converged) "CONVERGED" else "NOT_CONVERGED"
diagnostic$iterations <- if (is.null(model)) NA_integer_ else model$numIter
diagnostic$covariance_positive_definite <- covariance_ok
diagnostic$fit_error <- fit_error
diagnostic$fit_warnings <- paste(unique(fit_warnings), collapse = " | ")
utils::write.csv(diagnostic, args[[4]], row.names = FALSE)

if (!converged) {
  cat(
    "Full-lineage target-drug NLME fit failed convergence checks; ",
    "no comparison CSV was written.\n",
    "Diagnostics: ", args[[4]], "\n",
    sep = ""
  )
  stop("Do not interpret coefficients from this fit.")
}

coefficients <- as.data.frame(stats::coef(model))
groups <- strsplit(rownames(coefficients), "/", fixed = TRUE)
coefficients$COSMIC_ID <- as.numeric(vapply(groups, `[[`, character(1), 1))
drug_spec <- vapply(groups, `[[`, character(1), 2)
coefficients$DRUG_ID <- sub("_.*$", "", drug_spec)
coefficients$maxc <- as.numeric(sub("^[^_]*_", "", drug_spec))
coefficients$model_ln_ic50 <- log(coefficients$maxc) +
  (coefficients$xmid - 9) * log(2)

scan_keys <- stats::aggregate(
  viability_fraction ~ cell_line + cosmic_id + drug_id + scan_id,
  data = wells,
  FUN = function(values) min(values) < 0.5 && max(values) > 0.5
)
names(scan_keys)[names(scan_keys) == "viability_fraction"] <-
  "crosses_50_percent"
crossing_counts <- stats::aggregate(
  crosses_50_percent ~ cosmic_id + drug_id,
  data = scan_keys,
  FUN = sum
)
scan_counts <- stats::aggregate(
  scan_id ~ cosmic_id + drug_id,
  data = scan_keys,
  FUN = length
)
names(scan_counts)[names(scan_counts) == "scan_id"] <- "n_scans"

output <- merge(
  coefficients,
  reference[c("COSMIC_ID", "DRUG_ID", "CELL_LINE_NAME", "DRUG_NAME",
             "LN_IC50", "AUC", "RMSE")],
  by = c("COSMIC_ID", "DRUG_ID"),
  all = FALSE
)
output <- merge(
  output,
  crossing_counts,
  by.x = c("COSMIC_ID", "DRUG_ID"),
  by.y = c("cosmic_id", "drug_id"),
  all.x = TRUE
)
output <- merge(
  output,
  scan_counts,
  by.x = c("COSMIC_ID", "DRUG_ID"),
  by.y = c("cosmic_id", "drug_id"),
  all.x = TRUE
)
output$abs_difference_ln <- abs(output$model_ln_ic50 - output$LN_IC50)
output$fit_model_isLargeData <- is_large_data
output <- output[order(output$CELL_LINE_NAME, output$DRUG_ID), c(
  "CELL_LINE_NAME", "COSMIC_ID", "DRUG_ID", "DRUG_NAME", "n_scans",
  "crosses_50_percent", "xmid", "scal", "model_ln_ic50", "LN_IC50",
  "abs_difference_ln", "AUC", "RMSE", "fit_model_isLargeData"
)]
signed_difference_ln <- output$model_ln_ic50 - output$LN_IC50
has_scan_crossing <- output$crosses_50_percent > 0L
diagnostic$comparison_rows <- nrow(output)
diagnostic$pearson_correlation <- stats::cor(
  output$model_ln_ic50, output$LN_IC50
)
diagnostic$mean_signed_difference_ln <- mean(signed_difference_ln)
diagnostic$median_absolute_difference_ln <- stats::median(
  output$abs_difference_ln
)
diagnostic$max_absolute_difference_ln <- max(output$abs_difference_ln)
diagnostic$scan_drug_curve_count <- sum(output$n_scans)
diagnostic$scan_drug_curve_crossings_50_percent <-
  sum(output$crosses_50_percent)
diagnostic$combinations_with_any_scan_crossing <- sum(has_scan_crossing)
diagnostic$combinations_without_scan_crossing <- sum(!has_scan_crossing)
diagnostic$median_absolute_difference_ln_with_crossing <- stats::median(
  output$abs_difference_ln[has_scan_crossing]
)
diagnostic$median_absolute_difference_ln_without_crossing <- stats::median(
  output$abs_difference_ln[!has_scan_crossing]
)
diagnostic$mean_signed_difference_ln_with_crossing <-
  mean(signed_difference_ln[has_scan_crossing])
diagnostic$mean_signed_difference_ln_without_crossing <-
  mean(signed_difference_ln[!has_scan_crossing])
utils::write.csv(output, args[[3]], row.names = FALSE)
utils::write.csv(diagnostic, args[[4]], row.names = FALSE)
cat(
  "Model converged. Comparison rows:", nrow(output),
  "; comparison CSV:", args[[3]], "\n"
)
