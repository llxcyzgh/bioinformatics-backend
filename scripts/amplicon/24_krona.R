#!/usr/bin/env Rscript
# ============================================================
# Krona交互式分类组成图 (tool_id: amp-krona)
# 描述：生成Krona格式的分类组成数据，用于交互式可视化
#   输出Krona XML/TSV格式，可用Krona工具打开
# 输入：OTU表 (otu.tsv), taxonomy.tsv
# 输出：krona_data.tsv, krona_report.txt
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("dplyr", "tidyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
tax_file <- file.path(INPUT_DIR, "taxonomy.tsv")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(tax_file)) stop("错误：找不到taxonomy.tsv，Krona需要分类信息")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
tax_df <- read.table(tax_file, header = TRUE, row.names = 1, sep = "\t",
                      stringsAsFactors = FALSE, comment.char = "")

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

# 确保OTU名匹配
shared_otus <- intersect(rownames(otu_mat), rownames(tax_df))
otu_mat <- otu_mat[shared_otus, , drop = FALSE]
tax_df <- tax_df[shared_otus, , drop = FALSE]

cat(sprintf("数据：%d OTU，%d 样本\n", nrow(otu_mat), ncol(otu_mat)))

# ---- 定义分类层级 ----
taxa_ranks <- c("Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species")
taxa_ranks <- intersect(taxa_ranks, colnames(tax_df))
if (length(taxa_ranks) == 0) stop("错误：taxonomy.tsv中未找到标准分类层级列")

cat(sprintf("分类层级：%s\n", paste(taxa_ranks, collapse = " > ")))

# ---- 替换NA为"Unclassified" ----
for (col in taxa_ranks) {
  tax_df[[col]][is.na(tax_df[[col]])] <- "Unclassified"
  tax_df[[col]][tax_df[[col]] == ""] <- "Unclassified"
}

# ---- 生成Krona TSV格式 ----
# Krona TSV格式：丰度值 + 各层级分类名
krona_cols <- taxa_ranks
krona_data <- cbind(
  OTU_ID = rownames(otu_mat),
  tax_df[, krona_cols, drop = FALSE],
  otu_mat
)

# ---- 输出Krona TSV文件 ----
# 逐样本输出Krona格式
for (sample in colnames(otu_mat)) {
  sample_data <- data.frame(
    Abundance = otu_mat[, sample],
    tax_df[, krona_cols, drop = FALSE],
    stringsAsFactors = FALSE
  )
  sample_data <- sample_data[sample_data$Abundance > 0, ]
  sample_data <- sample_data[order(sample_data$Abundance, decreasing = TRUE), ]

  out_file <- file.path(OUTPUT_DIR, paste0("krona_", sample, ".tsv"))
  write.table(sample_data, out_file, sep = "\t", quote = FALSE, row.names = FALSE)
}

cat(sprintf("已生成 %d 个样本的Krona数据文件\n", ncol(otu_mat)))

# ---- 生成汇总Krona文件（所有样本合并）----
total_abund <- rowSums(otu_mat)
krona_all <- data.frame(
  Abundance = total_abund,
  tax_df[, krona_cols, drop = FALSE],
  stringsAsFactors = FALSE
)
krona_all <- krona_all[krona_all$Abundance > 0, ]
krona_all <- krona_all[order(krona_all$Abundance, decreasing = TRUE), ]

write.table(krona_all, file.path(OUTPUT_DIR, "krona_all_samples.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# ---- 输出报告 ----
report_lines <- c(
  sprintf("Krona数据生成报告"),
  sprintf("============="),
  sprintf("样本数：%d", ncol(otu_mat)),
  sprintf("OTU数：%d", nrow(otu_mat)),
  sprintf("分类层级：%s", paste(taxa_ranks, collapse = ", ")),
  sprintf("总序列数：%d", sum(otu_mat)),
  sprintf(""),
  sprintf("使用方法："),
  sprintf("  安装Krona: conda install -c bioconda krona"),
  sprintf("  导入数据: ktImportText krona_*.tsv -o krona.html"),
  sprintf("  或使用在线版: https://github.com/marbl/Krona/wiki")
)
writeLines(report_lines, file.path(OUTPUT_DIR, "krona_report.txt"))

cat("Krona数据生成完成\n")
cat("提示：使用 ktImportText 导入TSV文件生成交互式HTML\n")
