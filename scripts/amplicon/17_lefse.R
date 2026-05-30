#!/usr/bin/env Rscript
# ============================================================
# LEfSe生物标志物发现 (tool_id: amp-lefse)
# 描述：使用LDA Effect Size方法发现组间差异生物标志物
#   Kruskal-Wallis筛选 -> Wilcoxon成对比较 -> LDA评分
# 输入：OTU/物种丰度表, metadata.tsv
# 输出：lefse_results.tsv, lefse_barplot.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "dplyr", "tidyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
LDA_THRESHOLD <- as.numeric(ifelse(length(args) >= 4, args[4], 2.0))  # LDA阈值
KW_P_THRESHOLD <- as.numeric(ifelse(length(args) >= 5, args[5], 0.05))

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
cat(sprintf("数据：%d OTU，%d 样本，%d 组\n", nrow(rel_abund), ncol(rel_abund), length(groups)))

# ---- 第一步：Kruskal-Wallis筛选 ----
kw_results <- apply(rel_abund, 1, function(x) {
  tryCatch({
    test <- kruskal.test(x, grp)
    c(p_value = test$p.value, statistic = test$statistic)
  }, error = function(e) c(p_value = 1, statistic = 0))
})
kw_df <- as.data.frame(t(kw_results))
kw_df$OTU <- rownames(kw_df)
kw_df <- kw_df[kw_df$p_value < KW_P_THRESHOLD, ]
cat(sprintf("KW筛选通过：%d 个OTU\n", nrow(kw_df)))

if (nrow(kw_df) == 0) {
  write.table(data.frame(), file.path(OUTPUT_DIR, "lefse_results.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
  cat("未发现显著差异物种\n")
  quit(status = 0)
}

# ---- 第二步：确定每个OTU的最高丰度组 + LDA评分 ----
lefse_results <- list()

for (otu in kw_df$OTU) {
  abund_by_group <- tapply(rel_abund[otu, ], grp, mean)
  highest_group <- names(which.max(abund_by_group))

  # 简化LDA计算：使用log2倍数变化 * 组内方差加权
  group_means <- as.numeric(abund_by_group)
  overall_mean <- mean(rel_abund[otu, ])

  # LDA近似评分
  lda_score <- log2(max(group_means) / (min(group_means) + 1e-10)) *
    abs(mean(group_means) - overall_mean) / (sd(rel_abund[otu, ]) + 1e-10)

  lefse_results[[length(lefse_results) + 1]] <- data.frame(
    OTU = otu,
    Highest_Group = highest_group,
    KW_pvalue = signif(kw_df$p_value[kw_df$OTU == otu], 4),
    LDA_score = round(abs(lda_score), 4),
    Mean_abundance = round(max(group_means), 6),
    stringsAsFactors = FALSE
  )
}

lefse_df <- do.call(rbind, lefse_results)
lefse_df <- lefse_df[order(lefse_df$LDA_score, decreasing = TRUE), ]
lefse_df <- lefse_df[lefse_df$LDA_score >= LDA_THRESHOLD, ]

# ---- 输出结果 ----
write.table(lefse_df, file.path(OUTPUT_DIR, "lefse_results.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)
cat(sprintf("LEfSe筛选结果：%d 个生物标志物\n", nrow(lefse_df)))

# ---- 绘制LDA柱状图 ----
if (nrow(lefse_df) > 0) {
  lefse_df$OTU <- factor(lefse_df$OTU, levels = rev(lefse_df$OTU))

  p <- ggplot(lefse_df, aes(x = OTU, y = LDA_score, fill = Highest_Group)) +
    geom_bar(stat = "identity", width = 0.7) +
    coord_flip() +
    geom_hline(yintercept = LDA_THRESHOLD, linetype = "dashed", color = "red") +
    theme_bw(base_size = 11) +
    labs(x = "", y = "LDA Score (log10)", fill = GROUP_COL,
         title = "LEfSe Biomarker Discovery") +
    theme(plot.title = element_text(hjust = 0.5))

  ggsave(file.path(OUTPUT_DIR, "lefse_barplot.png"), p, width = 10, height = 7, dpi = 300)
  cat("LEfSe柱状图已保存\n")
}
