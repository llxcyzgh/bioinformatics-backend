#!/usr/bin/env Rscript
# ============================================================
# 物种组成热图 - 按样本 (tool_id: amp-taxasummary)
# 描述：绘制各样本的物种组成热图
#   行=物种，列=样本，按分类层级聚合
# 输入：OTU表 (otu.tsv), taxonomy.tsv
# 输出：taxa_heatmap_sample.png, taxa_heatmap_data.tsv
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
TAXA_LEVEL <- ifelse(length(args) >= 3, args[3], "Genus")
TOP_N      <- as.integer(ifelse(length(args) >= 4, args[4], 30))

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
tax_file <- file.path(INPUT_DIR, "taxonomy.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

# ---- 聚合到指定分类水平 ----
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

# 相对丰度
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")

# 取Top N高丰度分类群
mean_abund <- rowMeans(rel_abund)
top_taxa <- names(sort(mean_abund, decreasing = TRUE))[1:min(TOP_N, nrow(rel_abund))]
rel_abund <- rel_abund[top_taxa, , drop = FALSE]

cat(sprintf("热图：%d 分类单元 x %d 样本\n", nrow(rel_abund), ncol(rel_abund)))

# ---- 读取metadata ----
annotation_col <- NULL
annotation_colors <- NULL
if (file.exists(meta_file)) {
  meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
  if ("Sample" %in% colnames(meta) && "Group" %in% colnames(meta)) {
    shared <- intersect(colnames(rel_abund), meta$Sample)
    annotation_col <- data.frame(Group = factor(meta$Group[match(shared, meta$Sample)]))
    rownames(annotation_col) <- shared
    n_grp <- length(unique(annotation_col$Group))
    annotation_colors <- list(Group = setNames(
      brewer.pal(max(3, n_grp), "Set2")[1:n_grp],
      levels(annotation_col$Group)
    ))
    rel_abund <- rel_abund[, shared]
  }
}

# ---- Z-score标准化 ----
z_mat <- t(scale(t(as.matrix(rel_abund))))
z_mat[is.na(z_mat)] <- 0

# ---- 保存丰度数据 ----
write.table(round(as.matrix(rel_abund), 6),
            file.path(OUTPUT_DIR, "taxa_heatmap_data.tsv"),
            sep = "\t", quote = FALSE, col.names = NA)

# ---- 绘制热图 ----
col_anno <- if (!is.null(annotation_col)) annotation_col else NA
col_anno_colors <- if (!is.null(annotation_colors)) annotation_colors else NA

png(file.path(OUTPUT_DIR, "taxa_heatmap_sample.png"), width = 2000, height = 1200, res = 150)
pheatmap(z_mat,
         annotation_col = col_anno,
         annotation_colors = col_anno_colors,
         show_colnames = TRUE, show_rownames = TRUE,
         cluster_rows = TRUE, cluster_cols = TRUE,
         clustering_distance_rows = "euclidean",
         clustering_distance_cols = "euclidean",
         clustering_method = "average",
         color = colorRampPalette(c("navy", "white", "firebrick3"))(100),
         fontsize_row = 8, fontsize_col = 8,
         main = paste0("Taxa Composition Heatmap (", TAXA_LEVEL, ", by Sample)"))
dev.off()

cat("物种组成热图（按样本）已完成\n")
