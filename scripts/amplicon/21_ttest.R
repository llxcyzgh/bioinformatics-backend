#!/usr/bin/env Rscript
# ============================================================
# T检验与Wilcoxon检验 (tool_id: amp-ttest)
# 描述：对物种丰度进行组间T检验或Wilcoxon秩和检验
#   支持连续变量相关性分析（Spearman/Pearson）
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：ttest_results.tsv, ttest_heatmap.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "dplyr", "pheatmap", "reshape2")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
TEST_TYPE  <- ifelse(length(args) >= 4, args[4], "wilcox")  # t-test, wilcox
P_THRESHOLD <- as.numeric(ifelse(length(args) >= 5, args[5], 0.05))

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")
if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(meta_file)) stop("错误：找不到metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

# 相对丰度
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")
grp <- factor(meta[[GROUP_COL]])
groups <- levels(grp)

if (length(groups) != 2) {
  cat("警告：组数不为2，仅比较前两组\n")
  groups <- groups[1:2]
}
cat(sprintf("检验类型：%s，比较：%s vs %s\n", TEST_TYPE, groups[1], groups[2]))

# ---- 对每个OTU执行检验 ----
g1_idx <- which(grp == groups[1])
g2_idx <- which(grp == groups[2])

results <- list()

for (i in seq_len(nrow(rel_abund))) {
  otu_name <- rownames(rel_abund)[i]
  v1 <- as.numeric(rel_abund[i, g1_idx])
  v2 <- as.numeric(rel_abund[i, g2_idx])

  # 跳过低丰度
  if (mean(c(v1, v2)) < 0.001) next

  test_res <- tryCatch({
    if (TEST_TYPE == "t-test") {
      t.test(v1, v2, var.equal = FALSE)
    } else {
      wilcox.test(v1, v2, exact = FALSE)
    }
  }, error = function(e) NULL)

  if (is.null(test_res)) next

  results[[length(results) + 1]] <- data.frame(
    OTU = otu_name,
    Mean_Group1 = round(mean(v1), 6),
    Mean_Group2 = round(mean(v2), 6),
    Log2FC = round(log2((mean(v2) + 1e-10) / (mean(v1) + 1e-10)), 4),
    Statistic = round(test_res$statistic, 4),
    P_value = test_res$p.value,
    stringsAsFactors = FALSE
  )
}

if (length(results) == 0) stop("无足够数据进行检验")

result_df <- do.call(rbind, results)
result_df$P_adjusted <- p.adjust(result_df$P_value, method = "BH")
result_df$Significance <- ifelse(result_df$P_adjusted < P_THRESHOLD, "Significant", "NS")
result_df <- result_df[order(result_df$P_adjusted), ]

# ---- 输出结果 ----
write.table(result_df, file.path(OUTPUT_DIR, "ttest_results.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

sig_count <- sum(result_df$P_adjusted < P_THRESHOLD)
cat(sprintf("检验完成：%d 差异物种 (padj < %.2f)\n", sig_count, P_THRESHOLD))

# ---- 绘制显著物种热图 ----
sig_otus <- result_df$OTU[result_df$P_adjusted < P_THRESHOLD]
if (length(sig_otus) > 0) {
  sig_mat <- rel_abund[sig_otus[1:min(30, length(sig_otus))], ]
  # Z-score标准化
  z_mat <- t(scale(t(as.matrix(sig_mat))))

  # 按分组排序
  col_order <- order(grp)
  z_mat <- z_mat[, col_order]

  annotation_col <- data.frame(Group = grp[col_order])
  rownames(annotation_col) <- colnames(z_mat)

  png(file.path(OUTPUT_DIR, "ttest_heatmap.png"), width = 1200, height = 800, res = 150)
  pheatmap(z_mat, annotation_col = annotation_col,
           show_colnames = TRUE, show_rownames = TRUE,
           cluster_rows = TRUE, cluster_cols = FALSE,
           color = colorRampPalette(c("navy", "white", "firebrick3"))(100),
           main = paste0("Differential OTUs (", TEST_TYPE, ")"))
  dev.off()
  cat("差异物种热图已保存\n")
}
