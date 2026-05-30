#!/usr/bin/env Rscript
# ============================================================
# Alpha多样性指数计算 (tool_id: amp-alpha-data)
# 描述：基于OTU表计算多种Alpha多样性指数
#   包括Shannon, Simpson, Chao1, ACE, Richness, Pielou等
# 输入：OTU表 (otu.tsv)，可选metadata
# 输出：alpha_diversity.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("phyloseq", "vegan", "dplyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取OTU表 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
if (!file.exists(otu_file)) stop("错误：找不到OTU表文件 otu.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE, comment.char = ""))
# 确保为数值矩阵
otu_mat <- apply(otu_mat, 2, as.numeric)
rownames(otu_mat) <- rownames(read.table(otu_file, header = TRUE, row.names = 1,
                                          sep = "\t", check.names = FALSE))
# 去除全为0的OTU
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

cat(sprintf("读取OTU表：%d 个OTU，%d 个样本\n", nrow(otu_mat), ncol(otu_mat)))

# ---- 构建phyloseq对象 ----
OTU <- otu_table(otu_mat, taxa_are_rows = TRUE)
ps <- phyloseq(OTU)

# ---- 计算Alpha多样性指数 ----
# Shannon指数
shannon <- estimate_richness(ps, measures = "Shannon")
# Simpson指数（1 - Simpson）
simpson <- estimate_richness(ps, measures = "Simpson")
# Chao1指数
chao1 <- estimate_richness(ps, measures = "Chao1")
# ACE指数
ace <- estimate_richness(ps, measures = "ACE")
# Observed ASV/OTU数
observed <- estimate_richness(ps, measures = "Observed")

# Pielou均匀度 = Shannon / ln(Richness)
pielou <- data.frame(Pielou = shannon$Shannon / log(observed$Observed))
pielou[is.na(pielou)] <- 0

# Good覆盖度
good_cov <- data.frame(Good_Coverage = 1 - colSums(otu_mat == 1) / colSums(otu_mat))

# ---- 合并结果 ----
alpha_df <- data.frame(
  Sample = colnames(otu_mat),
  Shannon    = round(shannon$Shannon, 4),
  Simpson    = round(simpson$Simpson, 4),
  Chao1      = round(chao1$Chao1, 4),
  ACE        = round(ace$ACE, 4),
  Richness   = observed$Observed,
  Pielou     = round(pielou$Pielou, 4),
  Good_Coverage = round(good_cov$Good_Coverage, 4),
  stringsAsFactors = FALSE,
  row.names = NULL
)

# ---- 合并Metadata（如果存在）----
meta_file <- file.path(INPUT_DIR, "metadata.tsv")
if (file.exists(meta_file)) {
  meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
  if ("Sample" %in% colnames(meta)) {
    alpha_df <- merge(meta, alpha_df, by = "Sample", all.y = TRUE)
  }
}

# ---- 输出结果 ----
out_file <- file.path(OUTPUT_DIR, "alpha_diversity.tsv")
write.table(alpha_df, out_file, sep = "\t", quote = FALSE, row.names = FALSE)
cat(sprintf("Alpha多样性结果已保存至：%s\n", out_file))
cat(sprintf("共计算 %d 个样本的多样性指数\n", nrow(alpha_df)))
