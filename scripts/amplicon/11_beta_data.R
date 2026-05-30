#!/usr/bin/env Rscript
# ============================================================
# Beta多样性距离矩阵计算 (tool_id: amp-beta-data)
# 描述：计算样本间Beta多样性距离矩阵
#   支持Bray-Curtis, Jaccard, UniFrac等距离方法
# 输入：OTU表 (otu.tsv)，可选系统发育树 (tree.nwk)
# 输出：beta_distance.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("phyloseq", "vegan", "ape")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
METHOD     <- ifelse(length(args) >= 3, args[3], "bray")  # bray, jaccard, unifrac, wunifrac

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取OTU表 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
if (!file.exists(otu_file)) stop("错误：找不到OTU表文件 otu.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE, comment.char = ""))
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

cat(sprintf("读取OTU表：%d OTU，%d 样本\n", nrow(otu_mat), ncol(otu_mat)))

# ---- 构建phyloseq对象 ----
OTU <- otu_table(otu_mat, taxa_are_rows = TRUE)
ps <- phyloseq(OTU)

# ---- 尝试加载系统发育树（UniFrac需要）----
tree_file <- file.path(INPUT_DIR, "tree.nwk")
if (file.exists(tree_file) && METHOD %in% c("unifrac", "wunifrac")) {
  tree <- read.tree(tree_file)
  # 确保树tip名与OTU表匹配
  shared <- intersect(tree$tip.label, rownames(otu_mat))
  if (length(shared) > 10) {
    ps <- merge_phyloseq(OTU, phy_tree(tree))
    cat(sprintf("加载系统发育树，%d 个共享OTU\n", length(shared)))
  } else {
    cat("警告：树tip与OTU匹配不足10个，回退到Bray-Curtis\n")
    METHOD <- "bray"
  }
} else if (METHOD %in% c("unifrac", "wunifrac")) {
  cat("警告：未找到tree.nwk，回退到Bray-Curtis\n")
  METHOD <- "bray"
}

# ---- 计算距离矩阵 ----
cat(sprintf("计算距离矩阵，方法：%s\n", METHOD))

if (METHOD == "unifrac") {
  dist_mat <- UniFrac(ps, weighted = FALSE)
} else if (METHOD == "wunifrac") {
  dist_mat <- UniFrac(ps, weighted = TRUE)
} else {
  # 转置：vegan需要样本为行
  dist_mat <- vegdist(t(otu_mat), method = METHOD, na.rm = TRUE)
}

# ---- 输出距离矩阵 ----
dist_df <- as.matrix(dist_mat)
out_file <- file.path(OUTPUT_DIR, paste0("beta_", METHOD, "_distance.tsv"))
write.table(round(dist_df, 6), out_file, sep = "\t", quote = FALSE,
            row.names = TRUE, col.names = NA)

cat(sprintf("Beta多样性距离矩阵已保存至：%s\n", out_file))
cat(sprintf("距离矩阵维度：%d x %d\n", nrow(dist_df), ncol(dist_df)))
