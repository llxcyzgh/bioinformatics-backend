#!/usr/bin/env Rscript
# ============================================================
# UPGMA聚类树构建 (tool_id: amp-upgma)
# 描述：基于Beta多样性距离矩阵构建UPGMA层次聚类树
# 输入：距离矩阵 (beta_*_distance.tsv) 或 OTU表
# 输出：upgma_tree.nwk, upgma_tree.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("phyloseq", "vegan", "ape", "ggplot2", "ggtree")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
DIST_METHOD <- ifelse(length(args) >= 3, args[3], "bray")  # 距离方法

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取距离矩阵或从OTU表计算 ----
dist_file <- file.path(INPUT_DIR, paste0("beta_", DIST_METHOD, "_distance.tsv"))
if (!file.exists(dist_file)) {
  # 尝试从OTU表计算
  otu_file <- file.path(INPUT_DIR, "otu.tsv")
  if (!file.exists(otu_file)) stop("错误：找不到距离矩阵或OTU表")
  otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1,
                                   sep = "\t", check.names = FALSE))
  otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]
  dist_mat <- vegdist(t(otu_mat), method = DIST_METHOD)
  cat("从OTU表计算距离矩阵\n")
} else {
  dist_df <- read.table(dist_file, header = TRUE, row.names = 1, sep = "\t", check.names = FALSE)
  dist_mat <- as.dist(dist_df)
  cat("读取已有距离矩阵\n")
}

# ---- UPGMA聚类 ----
hc <- hclust(dist_mat, method = "average")  # average = UPGMA
upgma_tree <- as.phylo(hc)

cat(sprintf("UPGMA聚类完成，%d 个样本\n", length(upgma_tree$tip.label)))

# ---- 保存Newick树文件 ----
tree_file <- file.path(OUTPUT_DIR, "upgma_tree.nwk")
write.tree(upgma_tree, file = tree_file)
cat(sprintf("Newick树文件已保存：%s\n", tree_file))

# ---- 读取metadata用于着色 ----
meta <- NULL
meta_file <- file.path(INPUT_DIR, "metadata.tsv")
if (file.exists(meta_file)) {
  meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
}

# ---- 绘制聚类树图 ----
p <- ggtree(upgma_tree, layout = "rectangular", size = 0.8) +
  geom_tiplab(size = 3, hjust = -0.1) +
  xlim(0, max(upgma_tree$edge.length) * 1.3) +
  ggtitle(paste0("UPGMA聚类树 (", toupper(DIST_METHOD), ")")) +
  theme_tree2() +
  theme(plot.title = element_text(hjust = 0.5, size = 14))

# 如果有分组信息，添加tip颜色
if (!is.null(meta) && "Group" %in% colnames(meta)) {
  grp_info <- setNames(meta$Group, meta$Sample)
  p <- p %<+% meta + geom_tippoint(aes(color = Group), size = 2.5)
}

# ---- 保存图片 ----
fig_file <- file.path(OUTPUT_DIR, "upgma_tree.png")
ggsave(fig_file, p, width = 10, height = 6, dpi = 300)
cat(sprintf("聚类树图已保存：%s\n", fig_file))
