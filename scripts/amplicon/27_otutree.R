#!/usr/bin/env Rscript
# ============================================================
# OTU系统发育树热图 (tool_id: amp-otutree)
# 描述：结合OTU系统发育树和丰度热图的可视化
# 输入：OTU表 (otu.tsv), tree.nwk, metadata.tsv
# 输出：otutree_heatmap.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ape", "phyloseq", "ggplot2", "ggtree", "dplyr", "pheatmap")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
TOP_N      <- as.integer(ifelse(length(args) >= 3, args[3], 50))

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
tree_file <- file.path(INPUT_DIR, "tree.nwk")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(tree_file)) stop("错误：找不到系统发育树 tree.nwk")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
tree <- read.tree(tree_file)
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

cat(sprintf("数据：%d OTU，%d 样本\n", nrow(otu_mat), ncol(otu_mat)))

# ---- 筛选Top N高丰度OTU ----
mean_abund <- rowMeans(otu_mat)
top_otus <- names(sort(mean_abund, decreasing = TRUE))[1:min(TOP_N, nrow(otu_mat))]

# 确保树中有这些OTU
tree_tips <- tree$tip.label
available_otus <- intersect(top_otus, tree_tips)
if (length(available_otus) < 5) stop("错误：树与OTU表匹配的tip过少")

# 修剪树
tree_pruned <- keep.tip(tree, available_otus)
otu_sub <- otu_mat[available_otus, , drop = FALSE]

cat(sprintf("绘制 %d OTU的系统发育树热图\n", length(available_otus)))

# ---- 相对丰度 ----
rel_abund <- sweep(otu_sub, 2, colSums(otu_sub), "/")

# ---- 读取分组信息 ----
annotation_col <- NULL
if (file.exists(meta_file)) {
  meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
  if ("Sample" %in% colnames(meta) && "Group" %in% colnames(meta)) {
    shared <- intersect(colnames(rel_abund), meta$Sample)
    annotation_col <- data.frame(Group = meta$Group[match(shared, meta$Sample)])
    rownames(annotation_col) <- shared
    rel_abund <- rel_abund[, shared]
  }
}

# ---- 按树排序OTU ----
tree_order <- tree_pruned$tip.label
rel_abund <- rel_abund[tree_order, , drop = FALSE]

# ---- 使用ggtree + 热图 ----
# 绘制系统发育树
p_tree <- ggtree(tree_pruned, layout = "rectangular", size = 0.3) +
  geom_tiplab(size = 2, hjust = -0.05) +
  xlim_tree(max(node.depth.edgelength(tree_pruned)) * 1.4)

# 保存树+热图组合图
# 方法：分别保存树和热图，然后组合
png(file.path(OUTPUT_DIR, "otutree_heatmap.png"), width = 2400, height = 1600, res = 150)
layout(matrix(c(1, 2), nrow = 1), widths = c(1, 1.5))

# 左侧：系统发育树
par(mar = c(2, 0, 3, 0))
plot(tree_pruned, show.tip.label = TRUE, cex = 0.7,
     label.offset = 0.01, edge.width = 0.8)
title("Phylogenetic Tree", cex.main = 1.2)

# 右侧：热图
par(mar = c(2, 2, 3, 1))
z_mat <- t(scale(t(as.matrix(rel_abund))))
col_order <- if (!is.null(annotation_col)) order(annotation_col$Group) else seq_len(ncol(z_mat))
z_mat <- z_mat[, col_order]

image(1:ncol(z_mat), 1:nrow(z_mat), t(z_mat),
      col = colorRampPalette(c("navy", "white", "firebrick3"))(100),
      xlab = "", ylab = "", axes = FALSE,
      main = "Abundance Heatmap")
axis(1, at = 1:ncol(z_mat), labels = colnames(z_mat), las = 2, cex.axis = 0.7)
axis(2, at = 1:nrow(z_mat), labels = rownames(z_mat), las = 1, cex.axis = 0.5)

dev.off()

# ---- 同时保存ggtree版本 ----
ggsave(file.path(OUTPUT_DIR, "otutree_ggtree.png"), p_tree,
       width = 12, height = max(8, length(available_otus) * 0.15), dpi = 200)

cat("OTU系统发育树热图已完成\n")
