#!/usr/bin/env Rscript
# ============================================================
# 物种组成热图 - 按分组 (tool_id: amp-taxasummary-group)
# 描述：绘制各分组的物种组成热图（组内均值）
#   行=物种，列=分组
# 输入：OTU表 (otu.tsv), taxonomy.tsv, metadata.tsv
# 输出：taxa_heatmap_group.png, taxa_heatmap_group_data.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "pheatmap", "dplyr", "tidyr", "RColorBrewer")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
TAXA_LEVEL <- ifelse(length(args) >= 4, args[4], "Genus")
TOP_N      <- as.integer(ifelse(length(args) >= 5, args[5], 30))

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
tax_file <- file.path(INPUT_DIR, "taxonomy.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(meta_file)) stop("错误：按分组绘图需要metadata.tsv")

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
    cat(sprintf("按 %s 聚合：%d 分类单元\n", TAXA_LEVEL, nrow(otu_mat)))
  }
}

# 样本匹配
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

# 相对丰度
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")

# ---- 计算组内均值 ----
grp <- factor(meta[[GROUP_COL]])
group_means <- sapply(levels(grp), function(g) {
  idx <- which(grp == g)
  rowMeans(rel_abund[, idx, drop = FALSE])
})
group_means <- as.data.frame(group_means)
cat(sprintf("分组均值：%d 分类单元 x %d 组\n", nrow(group_means), ncol(group_means)))

# 取Top N
mean_abund <- rowMeans(group_means)
top_taxa <- names(sort(mean_abund, decreasing = TRUE))[1:min(TOP_N, nrow(group_means))]
group_means <- group_means[top_taxa, , drop = FALSE]

# ---- 保存数据 ----
write.table(round(group_means, 6),
            file.path(OUTPUT_DIR, "taxa_heatmap_group_data.tsv"),
            sep = "\t", quote = FALSE, col.names = NA)

# ---- Z-score标准化 ----
z_mat <- t(scale(t(as.matrix(group_means))))
z_mat[is.na(z_mat)] <- 0

# ---- 绘制热图 ----
png(file.path(OUTPUT_DIR, "taxa_heatmap_group.png"), width = 1200, height = 1200, res = 150)
pheatmap(z_mat,
         show_colnames = TRUE, show_rownames = TRUE,
         cluster_rows = TRUE, cluster_cols = FALSE,
         clustering_distance_rows = "euclidean",
         clustering_method = "average",
         color = colorRampPalette(c("navy", "white", "firebrick3"))(100),
         fontsize_row = 9, fontsize_col = 12,
         border_color = NA,
         main = paste0("Taxa Composition Heatmap (", TAXA_LEVEL, ", by Group)"))
dev.off()

cat("物种组成热图（按分组）已完成\n")
