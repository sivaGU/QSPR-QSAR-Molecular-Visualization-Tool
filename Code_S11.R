# ============================================================
# Williams plot workflow with spreadsheet input/output
# Files:
#   Insert TableS4.xlsx (ERB T50 data)
#   Insert TableS3.xlsx (ERA T50 data)
# Outputs:
#   Williams_<tag>.png, Williams_<tag>.csv, Williams_<tag>.xlsx
# ============================================================

options(pkgType = "binary", install.packages.check.source = "no")
need <- c("openxlsx","ggplot2")
inst <- setdiff(need, rownames(installed.packages()))
if (length(inst)) install.packages(inst, dependencies = TRUE)
library(openxlsx); library(ggplot2)

# Williams plot function
williams_from_model <- function(fit, title = "Williams Plot", id = NULL) {
  n <- length(residuals(fit))
  p <- length(coef(fit)) - 1L
  h <- hatvalues(fit)
  rstd <- rstandard(fit)
  h_star <- 3 * (p + 1) / n
  
  df <- data.frame(
    .row = seq_len(n),
    leverage = as.numeric(h),
    rstd = as.numeric(rstd)
  )
  if (!is.null(id) && length(id) == n) df <- cbind(ID = id, df)
  
  df$outside_residual <- abs(df$rstd) > 3
  df$outside_leverage <- df$leverage > h_star
  df$outside_any <- df$outside_residual | df$outside_leverage
  
  plt <- ggplot(df, aes(x = leverage, y = rstd)) +
    geom_hline(yintercept = c(-3, 3), linetype = "dashed") +
    geom_vline(xintercept = h_star, linetype = "dashed") +
    geom_point(aes(color = outside_any)) +
    scale_color_manual(values = c("FALSE" = "grey40", "TRUE" = "red")) +
    labs(title = title, x = "Leverage (h)", y = "Standardized residual", color = "Outside AD?") +
    theme_bw()
  
  list(df = df, h_star = h_star, plot = plt)
}

# Save plot and table
write_williams <- function(w_obj, out_dir, stem) {
  if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
  ggsave(file.path(out_dir, paste0(stem, ".png")),
         plot = w_obj$plot, width = 7, height = 5, dpi = 300)
  write.csv(w_obj$df, file.path(out_dir, paste0(stem, ".csv")), row.names = FALSE)
  wb <- openxlsx::createWorkbook()
  openxlsx::addWorksheet(wb, "Williams")
  openxlsx::writeData(wb, "Williams", w_obj$df)
  openxlsx::saveWorkbook(wb, file.path(out_dir, paste0(stem, ".xlsx")), overwrite = TRUE)
}

# ------------------------------------------------------------
# Example for ERB T50 (TableS4.xlsx)
# ------------------------------------------------------------
ERB_path <- "Insert TableS4.xlsx"
ERB <- openxlsx::read.xlsx(ERB_path, sheet = 1)

y_ERB <- names(ERB)[4]         # response variable
x_ERB <- names(ERB)[6:20]      # descriptor block

ERB[, c(y_ERB, x_ERB)] <- lapply(ERB[, c(y_ERB, x_ERB)], function(x) suppressWarnings(as.numeric(x)))
fit_ERB <- lm(reformulate(x_ERB, y_ERB), data = ERB, na.action = na.exclude)

w_ERB <- williams_from_model(fit_ERB, "Williams Plot: ERβ T50", id = ERB[[1]])
write_williams(w_ERB, out_dir = "outputs", stem = "Williams_ERB_T50")

# ------------------------------------------------------------
# Example for ERA T50 (TableS3.xlsx)
# ------------------------------------------------------------
ERA_path <- "Insert TableS3.xlsx"
ERA <- openxlsx::read.xlsx(ERA_path, sheet = 1)

y_ERA <- names(ERA)[4]
x_ERA <- names(ERA)[6:20]

ERA[, c(y_ERA, x_ERA)] <- lapply(ERA[, c(y_ERA, x_ERA)], function(x) suppressWarnings(as.numeric(x)))
fit_ERA <- lm(reformulate(x_ERA, y_ERA), data = ERA, na.action = na.exclude)

w_ERA <- williams_from_model(fit_ERA, "Williams Plot: ERα T50", id = ERA[[1]])
write_williams(w_ERA, out_dir = "outputs", stem = "Williams_ERA_T50")
