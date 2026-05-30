#!/usr/bin/env Rscript
# ============================================================
# Beta多样性显著性检验 (tool_id: amp-beta-div)
# 描述：对Beta多样性距离进行组间显著性检验
#   支持PERMANOVA (adonis), ANOSIM, MRPP等方法
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：beta_div_test.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("vegan", "phyloseq", "dplyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR   <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR  <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL   <- ifelse(length(args) >= 3, args[3], "Group")
DIST_METHOD <- ifelse(length(args) >= 4, args[4], "bray")

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")
if (!file.exists(otu_file)) stop("错误：找不到OTU表文件 otu.tsv")
if (!file.exists(meta_file)) stop("错误：找不到metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE, comment.char = ""))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

# 确保样本名一致
shared_samples <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared_samples]
meta <- meta[meta$Sample %in% shared_samples, ]

cat(sprintf("数据：%d OTU，%d 样本\n", nrow(otu_mat), length(shared_samples)))

# ---- 计算距离矩阵 ----
dist_mat <- vegdist(t(otu_mat), method = DIST_METHOD)

# ---- 分组因子 ----
grp <- factor(meta[[GROUP_COL]][match(colnames(otu_mat), meta$Sample)])
n_groups <- length(levels(grp))
cat(sprintf("分组：%s，共 %d 组\n", GROUP_COL, n_groups))

# ---- PERMANOVA检验 (adonis2) ----
set.seed(42)
permanova_res <- adonis2(dist_mat ~ grp, permutations = 999)
cat("PERMANOVA完成\n")

# ---- ANOSIM检验 ----
anosim_res <- anosim(dist_mat, grp, permutations = 999)
cat("ANOSIM完成\n")

# ---- MRPP检验 ----
mrpp_res <- mrpp(t(otu_mat), grp, distance = DIST_METHOD, permutations = 999)
cat("MRPP完成\n")

# ---- 整理结果 ----
result_df <- data.frame(
  Method = c("PERMANOVA", "ANOSIM", "MRPP"),
  Statistic = c(
    round(permanova_res$F[1], 4),
    round(anosim_res$statistic, 4),
    round(mrpp_res$delta, 4)
  ),
  R_squared = c(
    round(permanova_res$R2[1], 4),
    round(anosim_res$statistic, 4),
    round(mrpp_res$A, 4)
  ),
  P_value = c(
    signif(permanova_res$`Pr(>F)`[1], 4),
    signif(anosim_res$signif, 4),
    signif(mrpp_res$Pvalue, 4)
  ),
  Permutations = c(999, 999, 999),
  Distance = DIST_METHOD,
  stringsAsFactors = FALSE
)

# ---- 输出结果 ----
out_file <- file.path(OUTPUT_DIR, "beta_div_test.tsv")
write.table(result_df, out_file, sep = "\t", quote = FALSE, row.names = FALSE)
cat(sprintf("Beta多样性检验结果已保存：%s\n", out_file))

# 打印摘要
print(result_df)
