#!/usr/bin/env Rscript
# ============================================================
# 三元相图 (tool_id: amp-ternary)
# 描述：绘制三元相图展示三组样本的物种丰度分布
#   顶点代表三组，点代表物种，位置表示在三组中的相对丰度
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：ternary_plot.png, ternary_data.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "ggtern", "dplyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    if (pkg == "ggtern") {
      install.packages(pkg, repos = "https://cloud.r-project.org")
    } else {
      install.packages(pkg, repos = "https://cloud.r-project.org")
    }
  }
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
TAXA_LEVEL <- ifelse(length(args) >= 4, args[4], "Genus")

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
tax_file <- file.path(INPUT_DIR, "taxonomy.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(meta_file)) stop("错误：三元相图需要metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

# ---- 聚合到分类水平 ----
if (file.exists(tax_file)) {
  tax_df <- read.table(tax_file, header = TRUE, row.names = 1, sep = "\t",
                        stringsAsFactors = FALSE, comment.char = "")
  if (TAXA_LEVEL %in% colnames(tax_df)) {
    taxa_assignments <- tax_df[[TAXA_LEVEL]]
    taxa_assignments[is.na(taxa_assignments)] <- "Unclassified"
    shared_otus <- intersect(rownames(otu_mat), rownames(tax_df))
    otu_sub <- otu_mat[shared_otus, , drop = FALSE]
    taxa_sub <- taxa_assignments[match(shared_otus, rownames(tax_df))]
    otu_mat <- rowsum(otu_sub, group = taxa_sub)
  }
}

# 样本匹配
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

# 相对丰度
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")

# ---- 选择三组 ----
grp <- factor(meta[[GROUP_COL]])
groups <- levels(grp)

if (length(groups) < 3) stop("错误：三元相图需要至少3个分组")
if (length(groups) > 3) {
  cat(sprintf("警告：共 %d 组，仅使用前3组：%s\n",
              length(groups), paste(groups[1:3], collapse = ", ")))
  groups <- groups[1:3]
}

# ---- 计算组内均值 ----
group_abund <- sapply(groups, function(g) {
  idx <- which(grp == g)
  rowMeans(rel_abund[, idx, drop = FALSE])
})
colnames(group_abund) <- c("T1", "T2", "T3")

# 标准化到0-1（每个物种在三组中的比例）
row_sums <- rowSums(group_abund)
ternary_data <- group_abund / row_sums
ternary_data[is.na(ternary_data)] <- 0

# 过滤低丰度
ternary_data <- ternary_data[row_sums > 0.001, ]

# 加上物种名
ternary_df <- as.data.frame(ternary_data)
ternary_df$Taxa <- rownames(ternary_df)
ternary_df$Total_Abundance <- row_sums[rownames(ternary_df)]

# ---- 保存数据 ----
write.table(ternary_df, file.path(OUTPUT_DIR, "ternary_data.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

cat(sprintf("三元相图数据：%d 分类单元，3 组 (%s)\n", nrow(ternary_df), paste(groups, collapse = "/")))

# ---- 绘制三元相图 ----
# 重新命名列以匹配三组
colnames(ternary_df)[1:3] <- groups

p <- ggtern(ternary_df, aes(x = !!sym(groups[1]), y = !!sym(groups[2]), z = !!sym(groups[3]))) +
  geom_point(aes(size = Total_Abundance), alpha = 0.6, color = "steelblue") +
  theme_rgbw(base_size = 12) +
  labs(title = paste0("Ternary Plot (", paste(groups, collapse = " vs "), ")"),
       x = groups[1], y = groups[2], z = groups[3],
       size = "Mean Abundance") +
  theme(plot.title = element_text(hjust = 0.5, size = 14))

ggsave(file.path(OUTPUT_DIR, "ternary_plot.png"), p, width = 10, height = 9, dpi = 300)
cat("三元相图已完成\n")
