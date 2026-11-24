#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) {
  stop(
    "Usage: compare_gdsc2_pdac_subset_gdscic50.R ",
    "<curve_points.csv> <GDSC2_fitted_dose_response_24Jul22.csv> <output.csv>"
  )
}
if (file.exists(args[[3]])) {
  stop("Output already exists; choose a new output path.")
}

if (!requireNamespace("gdscIC50", quietly = TRUE)) {
  stop("Install the official CancerRxGene/gdscIC50 package before running.")
}
if (as.character(utils::packageVersion("gdscIC50")) != "0.99.4") {
  stop("This comparison was checked with gdscIC50 version 0.99.4.")
}
library(gdscIC50)

points <- utils::read.csv(args[[1]], stringsAsFactors = FALSE)
reference <- utils::read.csv(args[[2]], stringsAsFactors = FALSE)

required_points <- c(
  "scan_id", "cosmic_id", "cell_line", "drug_id", "drug_name",
  "drugset_id", "library_tag", "concentration_uM",
  "mean_viability_fraction"
)
if (!all(required_points %in% names(points))) {
  stop("The curve-points CSV is missing required extractor columns.")
}
required_reference <- c(
  "DATASET", "COSMIC_ID", "DRUG_ID", "DRUG_NAME", "MAX_CONC",
  "LN_IC50", "AUC", "RMSE"
)
if (!all(required_reference %in% names(reference))) {
  stop("The fitted-dose-response CSV is missing required GDSC2 columns.")
}
if (any(!is.finite(points$concentration_uM)) ||
    any(points$concentration_uM <= 0) ||
    any(!is.finite(points$mean_viability_fraction))) {
  stop("Dose and viability values must be finite; doses must be positive.")
}

cell_line_ids <- c("AsPC-1" = 910702, "BxPC-3" = 906693, "CAPAN-1" = 753624)
drug_ids <- c("1005", "1017", "1073", "1080", "1190")
points$drug_id <- as.character(points$drug_id)
points$cosmic_id <- as.numeric(points$cosmic_id)
points <- points[
  points$cell_line %in% names(cell_line_ids) &
    points$drug_id %in% drug_ids,
  ,
  drop = FALSE
]
if (nrow(points) == 0L) {
  stop("No target cell-line/drug curves were found.")
}
if (any(points$cosmic_id != unname(cell_line_ids[points$cell_line]))) {
  stop("Cell-line names do not match the configured COSMIC identifiers.")
}

reference <- reference[
  reference$DATASET == "GDSC2" &
    reference$COSMIC_ID %in% unname(cell_line_ids) &
    as.character(reference$DRUG_ID) %in% drug_ids,
  ,
  drop = FALSE
]
reference$DRUG_ID <- as.character(reference$DRUG_ID)
if (anyDuplicated(paste(reference$COSMIC_ID, reference$DRUG_ID, sep = "_"))) {
  stop("The fitted reference has duplicate target cell-line/drug rows.")
}
if (nrow(reference) != length(unique(paste(
  points$cosmic_id, points$drug_id, sep = "_"
)))) {
  stop("The fitted reference does not cover every extracted target curve.")
}

for (drug_id in drug_ids) {
  reference_max <- unique(reference$MAX_CONC[
    as.character(reference$DRUG_ID) == drug_id
  ])
  observed_max <- max(points$concentration_uM[points$drug_id == drug_id])
  if (length(reference_max) != 1L ||
      !isTRUE(all.equal(observed_max, reference_max, tolerance = 1e-10))) {
    stop("Observed maximum concentration does not match GDSC2 for drug ", drug_id)
  }
}

max_concentration <- setNames(
  vapply(drug_ids, function(drug_id) {
    unique(reference$MAX_CONC[as.character(reference$DRUG_ID) == drug_id])
  }, numeric(1)),
  drug_ids
)
points$maxc <- unname(max_concentration[points$drug_id])
points$x <- log2(points$concentration_uM / points$maxc) + 9
points$y <- 1 - points$mean_viability_fraction
points$CL <- as.character(points$cosmic_id)
points$drug <- paste(
  points$drug_id,
  format(points$maxc, digits = 15, scientific = FALSE, trim = TRUE),
  sep = "_"
)

model_data <- points[c("CL", "x", "y", "drug", "maxc")]
fit_warnings <- character()
model <- withCallingHandlers(
  gdscIC50::fitModelNlmeData(model_data, isLargeData = FALSE),
  warning = function(warning) {
    fit_warnings <<- c(fit_warnings, conditionMessage(warning))
    invokeRestart("muffleWarning")
  }
)
if (model$numIter >= 50L || is.character(model$apVar) ||
    any(grepl("converg|iteration", fit_warnings, ignore.case = TRUE))) {
  cat(
    "The subset NLME fit did not pass convergence checks; no comparison ",
    "CSV was written.\n",
    "iterations: ", model$numIter, "\n",
    "approximate covariance status: ",
    if (is.character(model$apVar)) model$apVar else "available", "\n",
    "warnings: ", paste(fit_warnings, collapse = " | "), "\n",
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
coefficients$model_subset_ln_ic50 <- log(coefficients$maxc) +
  (coefficients$xmid - 9) * log(2)

scan_keys <- unique(points[c("cell_line", "drug_id", "scan_id")])
scan_keys$crosses_50_percent <- mapply(
  function(cell_line, drug_id, scan_id) {
    values <- points$mean_viability_fraction[
      points$cell_line == cell_line &
        points$drug_id == drug_id &
        points$scan_id == scan_id
    ]
    min(values) < 0.5 && max(values) > 0.5
  },
  scan_keys$cell_line,
  scan_keys$drug_id,
  scan_keys$scan_id
)
crossing_counts <- stats::aggregate(
  crosses_50_percent ~ cell_line + drug_id,
  data = scan_keys,
  FUN = sum
)
scan_counts <- stats::aggregate(
  scan_id ~ cell_line + drug_id,
  data = scan_keys,
  FUN = length
)
names(scan_counts)[names(scan_counts) == "scan_id"] <- "n_scans"

output <- merge(
  coefficients,
  reference[c("COSMIC_ID", "DRUG_ID", "DRUG_NAME", "LN_IC50", "AUC", "RMSE")],
  by = c("COSMIC_ID", "DRUG_ID"),
  all = FALSE
)
output <- merge(
  output,
  data.frame(
    cell_line = names(cell_line_ids),
    COSMIC_ID = unname(cell_line_ids)
  ),
  by = "COSMIC_ID",
  all.x = TRUE
)
output <- merge(
  output,
  crossing_counts,
  by.x = c("cell_line", "DRUG_ID"),
  by.y = c("cell_line", "drug_id"),
  all.x = TRUE
)
output <- merge(
  output,
  scan_counts,
  by.x = c("cell_line", "DRUG_ID"),
  by.y = c("cell_line", "drug_id"),
  all.x = TRUE
)
output$abs_difference_ln <- abs(
  output$model_subset_ln_ic50 - output$LN_IC50
)
output$model_isLargeData <- FALSE
output <- output[order(output$cell_line, output$DRUG_ID), c(
  "cell_line", "COSMIC_ID", "DRUG_ID", "DRUG_NAME", "n_scans",
  "crosses_50_percent", "xmid", "scal", "model_subset_ln_ic50",
  "LN_IC50", "abs_difference_ln", "AUC", "RMSE", "model_isLargeData"
)]
utils::write.csv(output, args[[3]], row.names = FALSE)

cat(
  "gdscIC50 version:", as.character(utils::packageVersion("gdscIC50")), "\n",
  "model rows:", nrow(model_data), "\n",
  "cell lines:", length(unique(model_data$CL)), "\n",
  "drug groups:", length(unique(model_data$drug)), "\n",
  "small-screen model; AIC:", stats::AIC(model),
  "BIC:", stats::BIC(model), "\n",
  "scan curves crossing 50% viability:",
  sum(scan_keys$crosses_50_percent), "of", nrow(scan_keys), "\n",
  "comparison written to:", args[[3]], "\n",
  sep = ""
)
