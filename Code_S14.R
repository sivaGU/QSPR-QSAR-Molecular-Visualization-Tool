# ============================================================
# ALE bounds (CE / Table S5) — exports 3 XLSX files
# Input:
#   Insert TableS5.xlsx   (sheet 1)
#   ERA (ERα) response = column 4 (D)
#   ERB (ERβ) response = column 7 (G)
#   Descriptors = columns 8:18 (H:R)
# Outputs (to ./outputs):
#   ALE_bounds_ERB_from_S5.xlsx
#   ALE_bounds_ERA_from_S5.xlsx
#   ALE_bounds_S5_combined.xlsx
# ============================================================

set.seed(123)
options(pkgType = "binary", install.packages.check.source = "no")
need <- c("openxlsx","ggplot2","dplyr","tibble","iml","stringr")
inst <- setdiff(need, rownames(installed.packages()))
if (length(inst)) install.packages(inst, dependencies = TRUE)
suppressPackageStartupMessages({
  library(openxlsx); library(ggplot2); library(dplyr)
  library(tibble);   library(iml);     library(stringr)
})

theme_set(theme_bw(base_size = 13))

# ----------------------------
# Config
# ----------------------------
S5_XLSX  <- "Insert TableS5.xlsx"
SHEET    <- 1
OUT_ROOT <- "outputs"
DESC_IDX <- 8:18       # H:R
GRIDSIZE <- 20
if (!dir.exists(OUT_ROOT)) dir.create(OUT_ROOT, recursive = TRUE)

# ----------------------------
# Helpers
# ----------------------------
mk_name_map <- function(df) setNames(make.names(names(df), unique = TRUE), names(df))

force_numeric <- function(x) {
  if (is.numeric(x)) return(x)
  x <- gsub("\u2212", "-", x)
  x <- gsub(",", "", x)
  suppressWarnings(as.numeric(x))
}

full_rank_cols <- function(df, cols) {
  if (!length(cols)) return(character(0))
  X <- as.matrix(df[, cols, drop = FALSE])
  keep_nz <- sapply(cols, function(cn) {
    v <- X[, cn]
    if (all(is.na(v))) return(FALSE)
    s <- stats::sd(v, na.rm = TRUE)
    is.finite(s) && s > 0
  })
  cols2 <- cols[keep_nz]
  if (!length(cols2)) return(character(0))
  X2 <- as.matrix(df[, cols2, drop = FALSE])
  cc <- stats::complete.cases(X2)
  if (!any(cc)) return(cols2)
  qrX <- qr(scale(X2[cc, , drop = FALSE]))
  keep_idx <- sort(qrX$pivot[seq_len(qrX$rank)])
  cols2[keep_idx]
}

build_predictor <- function(fit, df_san, dv_san) {
  ivs <- attr(terms(fit), "term.labels")
  iml::Predictor$new(
    model = fit,
    data  = df_san[, ivs, drop = FALSE],
    y     = df_san[[dv_san]],
    predict.function = function(mod, newdata) as.numeric(predict(mod, newdata = newdata))
  )
}

ale_bounds_one <- function(predictor, feature_san, feature_orig, grid.size = GRIDSIZE) {
  fe <- iml::FeatureEffect$new(predictor, feature = feature_san, method = "ale", grid.size = grid.size)
  df <- fe$results
  ycol <- intersect(c(".value", ".y", "yhat", ".ale"), names(df))
  ycol <- if (length(ycol)) ycol[1] else ".value"
  
  # Prefer the exact feature column for X; fallback to first numeric non-meta column
  meta_cols <- c(".type", ".feature", ".class", ".id", ycol)
  if (feature_san %in% names(df) && is.numeric(df[[feature_san]])) {
    xcol <- feature_san
  } else {
    x_candidates <- setdiff(names(df), meta_cols)
    x_candidates <- x_candidates[sapply(df[x_candidates], is.numeric)]
    if (!length(x_candidates)) {
      return(tibble(
        Descriptor = feature_orig, Resolved = feature_san,
        X_min = NA_real_, X_max = NA_real_,
        ALE_min = NA_real_, ALE_max = NA_real_,
        ALE_range = NA_real_, Note = "X grid column not found"
      ))
    }
    xcol <- x_candidates[1]
  }
  
  tibble(
    Descriptor = feature_orig, Resolved = feature_san,
    X_min = suppressWarnings(min(df[[xcol]], na.rm = TRUE)),
    X_max = suppressWarnings(max(df[[xcol]], na.rm = TRUE)),
    ALE_min = suppressWarnings(min(df[[ycol]], na.rm = TRUE)),
    ALE_max = suppressWarnings(max(df[[ycol]], na.rm = TRUE))
  ) %>%
    mutate(ALE_range = ALE_max - ALE_min, Note = NA_character_)
}

# ----------------------------
# Run once per target (ERA / ERB)
# ----------------------------
run_on_s5 <- function(xlsx_path, y_col, desc_idx = DESC_IDX, sheet = 1) {
  raw_df <- openxlsx::read.xlsx(xlsx_path, sheet = sheet)
  stopifnot(is.data.frame(raw_df))
  orig_names <- names(raw_df)
  
  if (y_col < 1 || y_col > ncol(raw_df)) stop("y_col out of range for: ", xlsx_path)
  dv_idx  <- y_col
  dv_orig <- orig_names[dv_idx]
  
  if (max(desc_idx) > ncol(raw_df)) stop("DESC_IDX exceeds number of columns in S5.")
  desc_orig <- setdiff(unique(orig_names[desc_idx]), dv_orig)
  
  nmap   <- mk_name_map(raw_df)
  df_san <- raw_df; names(df_san) <- unname(nmap)
  dv_san <- unname(nmap[dv_orig])
  desc_san_all <- unique(na.omit(unname(nmap[desc_orig])))
  
  df_san[, c(dv_san, desc_san_all)] <- lapply(df_san[, c(dv_san, desc_san_all), drop = FALSE], force_numeric)
  
  desc_san_keep <- full_rank_cols(df_san, desc_san_all)
  map_tbl <- tibble(orig = desc_orig, san_all = unname(nmap[desc_orig])) %>%
    filter(san_all %in% desc_san_keep) %>%
    transmute(orig, san = san_all)
  
  form <- reformulate(map_tbl$san, dv_san)
  fit  <- lm(form, data = df_san, na.action = na.exclude)
  pred <- build_predictor(fit, df_san, dv_san)
  
  rows <- lapply(seq_len(nrow(map_tbl)), function(i) {
    ale_bounds_one(pred, map_tbl$san[i], map_tbl$orig[i], grid.size = GRIDSIZE)
  })
  bounds <- bind_rows(rows)
  
  list(bounds = bounds, map = map_tbl, dv_orig = dv_orig)
}

# ERA (ERα) = col 4 (D)
res_ERA_S5 <- run_on_s5(S5_XLSX, y_col = 4, desc_idx = DESC_IDX, sheet = SHEET)
# ERB (ERβ) = col 7 (G)
res_ERB_S5 <- run_on_s5(S5_XLSX, y_col = 7, desc_idx = DESC_IDX, sheet = SHEET)

# ----------------------------
# Common descriptors
# ----------------------------
norm_key <- function(v) {
  v %>%
    as.character() %>%
    stringr::str_trim() %>%
    stringr::str_squish() %>%
    { gsub("\u00A0", " ", ., fixed = TRUE) } %>%
    { gsub("[^A-Za-z0-9]+", "", .) } %>%
    toupper()
}
keys_ERB <- tibble(Descriptor = res_ERB_S5$map$orig, key = norm_key(res_ERB_S5$map$orig)) %>% distinct()
keys_ERA <- tibble(Descriptor = res_ERA_S5$map$orig, key = norm_key(res_ERA_S5$map$orig)) %>% distinct()

common_keys <- intersect(keys_ERB$key, keys_ERA$key)
if (!length(common_keys)) stop("No common descriptors after filtering.")

common_ERB_labels <- keys_ERB %>% filter(key %in% common_keys) %>% pull(Descriptor) %>% unique()
common_ERA_labels <- keys_ERA %>% filter(key %in% common_keys) %>% pull(Descriptor) %>% unique()

sel_cols <- c("Descriptor","Resolved","X_min","X_max","ALE_min","ALE_max","ALE_range","Note")

erb_common_bounds <- res_ERB_S5$bounds %>%
  filter(Descriptor %in% common_ERB_labels) %>%
  select(any_of(sel_cols)) %>%
  arrange(Descriptor)

era_common_bounds <- res_ERA_S5$bounds %>%
  filter(Descriptor %in% common_ERA_labels) %>%
  select(any_of(sel_cols)) %>%
  arrange(Descriptor)

if (nrow(erb_common_bounds) == 0 || nrow(era_common_bounds) == 0) {
  stop("Zero rows after common filtering. Check S5 headers and indices 8:18.")
}

# ----------------------------
# Combined side-by-side table
# ----------------------------
erb_for_join <- erb_common_bounds %>%
  select(Descriptor, X_min, X_max, ALE_min, ALE_max, ALE_range) %>%
  rename_with(~paste0(.x, "_ERB"), -Descriptor)

era_for_join <- era_common_bounds %>%
  select(Descriptor, X_min, X_max, ALE_min, ALE_max, ALE_range) %>%
  rename_with(~paste0(.x, "_ERA"), -Descriptor)

combined <- full_join(erb_for_join, era_for_join, by = "Descriptor") %>%
  arrange(Descriptor)

# ----------------------------
# Write XLSX files
# ----------------------------
out_ERB_xlsx  <- file.path(OUT_ROOT, "ALE_bounds_ERB_from_S5.xlsx")
out_ERA_xlsx  <- file.path(OUT_ROOT, "ALE_bounds_ERA_from_S5.xlsx")
out_COMB_xlsx <- file.path(OUT_ROOT, "ALE_bounds_S5_combined.xlsx")

wb1 <- openxlsx::createWorkbook(); openxlsx::addWorksheet(wb1, "ERB_common")
openxlsx::writeData(wb1, "ERB_common", erb_common_bounds)
openxlsx::saveWorkbook(wb1, out_ERB_xlsx, overwrite = TRUE)

wb2 <- openxlsx::createWorkbook(); openxlsx::addWorksheet(wb2, "ERA_common")
openxlsx::writeData(wb2, "ERA_common", era_common_bounds)
openxlsx::saveWorkbook(wb2, out_ERA_xlsx, overwrite = TRUE)

wb3 <- openxlsx::createWorkbook(); openxlsx::addWorksheet(wb3, "Combined")
openxlsx::writeData(wb3, "Combined", combined)
openxlsx::saveWorkbook(wb3, out_COMB_xlsx, overwrite = TRUE)

message("Wrote: ", out_ERB_xlsx, " | ", out_ERA_xlsx, " | ", out_COMB_xlsx)
