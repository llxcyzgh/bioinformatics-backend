#!/usr/bin/env Rscript
# ============================================================
# 群落差异多变量统计检验 (tool_id: amp-catecomp)
# 描述：基于物种丰度表进行多变量群落差异分析
#   包括MANOVA、多组置换检验、组间成对比较
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：catecomp_test.tsv, catecomp_pairwise.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("vegan", "dplyr", "tidyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
TAXA_LEVEL <- ifelse(length(args) >= 4, args[4], "Genus")  # 分类水平

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
tax_file <- file.path(INPUT_DIR, "taxonomy.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(meta_file)) stop("错误：找不到metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

# ---- 聚合到指定分类水平 ----
if (file.exists(tax_file)) {
  tax_df <- read.table(tax_file, header = TRUE, row.names = 1, sep = "\t",
                        stringsAsFactors = FALSE, comment.char = "")
  if (TAXA_LEVEL %in% colnames(tax_df)) {
    # 按分类水平聚合
    taxa_assignments <- tax_df[[TAXA_LEVEL]]
    taxa_assignments[is.na(taxa_assignments)] <- "Unclassified"
    agg_mat <- aggregate(rowsum(otu_mat, group = taxa_assignments))
    # 用rowsum聚合
    agg_mat <- rowsum(otu_mat, group = taxa_assignments)
    cat(sprintf("按 %s 水平聚合：%d 个分类单元\n", TAXA_LEVEL, nrow(agg_mat)))
    otu_mat <- agg_mat
  }
}

# 确保样本匹配
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

# 相对丰度
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")
# 只保留高丰度分类群（均值>0.01）
rel_abund <- rel_abund[rowMeans(rel_abund) > 0.01, , drop = FALSE]

cat(sprintf("分析 %d 个高丰度分类单元，%d 样本\n", nrow(rel_abund), ncol(rel_abund)))

# ---- MANOVA ----
data_t <- t(rel_abund)
grp <- factor(meta[[GROUP_COL]])
manova_res <- manova(data_t ~ grp)
manova_summary <- summary(manova_res, test = "Pillai")

cat(sprintf("MANOVA Pillai: %.4f, p = %.4f\n",
            manova_summary$stats[1, 2], manova_summary$stats[1, 6]))

# ---- 成对PERMANOVA ----
groups <- levels(grp)
pair_results <- list()

if (length(groups) >= 2) {
  for (i in 1:(length(groups) - 1)) {
    for (j in (i + 1):length(groups)) {
      pair_samples <- which(grp %in% c(groups[i], groups[j]))
      pair_dist <- vegdist(data_t[pair_samples, ], method = "bray")
      pair_grp <- droplevels(grp[pair_samples])
      set.seed(42)
      pair_adonis <- adonis2(pair_dist ~ pair_grp, permutations = 999)
      pair_results[[length(pair_results) + 1]] <- data.frame(
        Group1 = groups[i], Group2 = groups[j],
        R2 = round(pair_adonis$R2[1], 4),
        F_stat = round(pair_adonis$F[1], 4),
        P_value = signif(pair_adonis$`Pr(>F)`[1], 4),
        stringsAsFactors = FALSE
      )
    }
  }
}

# ---- 输出结果 ----
overall_df <- data.frame(
  Method = "MANOVA", Test = "Pillai",
  Statistic = round(manova_summary$stats[1, 2], 4),
  F_value = round(manova_summary$stats[1, 3], 4),
  P_value = signif(manova_summary$stats[1, 6], 4),
  stringsAsFactors = FALSE
)
write.table(overall_df, file.path(OUTPUT_DIR, "catecomp_test.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

if (length(pair_results) > 0) {
  pair_df <- do.call(rbind, pair_results)
  write.table(pair_df, file.path(OUTPUT_DIR, "catecomp_pairwise.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
}

cat("群落差异分析完成\n")
