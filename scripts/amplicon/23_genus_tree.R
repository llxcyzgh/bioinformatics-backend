#!/usr/bin/env Rscript
# ============================================================
# 属水平系统发育树 (tool_id: amp-genus-tree)
# 描述：构建属水平系统发育树，结合丰度热图
# 输入：OTU表 (otu.tsv), taxonomy.tsv, tree.nwk
# 输出：genus_tree.png, genus_tree.nwk
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ape", "phyloseq", "ggplot2", "ggtree", "dplyr")
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
tree_file <- file.path(INPUT_DIR, "tree.nwk")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(tree_file)) stop("错误：找不到系统发育树 tree.nwk")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
tree <- read.tree(tree_file)
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

cat(sprintf("OTU表：%d OTU，树：%d tips\n", nrow(otu_mat), length(tree$tip.label)))

# ---- 读取分类信息并聚合到属水平 ----
genus_assignments <- NULL
if (file.exists(tax_file)) {
  tax_df <- read.table(tax_file, header = TRUE, row.names = 1, sep = "\t",
                        stringsAsFactors = FALSE, comment.char = "")
  if ("Genus" %in% colnames(tax_df)) {
    genus_assignments <- tax_df$Genus
    names(genus_assignments) <- rownames(tax_df)
  }
}

# ---- 构建phyloseq对象 ----
OTU <- otu_table(otu_mat, taxa_are_rows = TRUE)

if (!is.null(genus_assignments)) {
  tax_mat <- tax_matrix(genus_assignments)
  TAX <- tax_table(tax_mat)
  ps <- phyloseq(OTU, TAX, phy_tree(tree))
} else {
  ps <- phyloseq(OTU, phy_tree(tree))
}

# 过滤低丰度
ps <- prune_taxa(taxa_sums(ps) > 0, ps)

# 取Top50丰度OTU
top_taxa <- names(sort(taxa_sums(ps), decreasing = TRUE))[1:min(50, ntaxa(ps))]
ps_top <- prune_taxa(top_taxa, ps)

cat(sprintf("绘制Top %d OTU的系统发育树\n", length(top_taxa)))

# ---- 绘制系统发育树 ----
tree_plot <- ggtree(ps_top, layout = "rectangular", size = 0.5) +
  geom_tiplab(size = 2.5, hjust = -0.05) +
  xlim_tree(max(node.depth.edgelength(phy_tree(ps_top))) * 1.3) +
  theme_tree2() +
  ggtitle("Genus-level Phylogenetic Tree") +
  theme(plot.title = element_text(hjust = 0.5, size = 14))

# 如果有分类信息，添加tip颜色
if (!is.null(genus_assignments)) {
  tax_df_top <- as.data.frame(tax_table(ps_top))
  tax_df_top$OTU <- rownames(tax_df_top)
  tree_plot <- tree_plot %<+% tax_df_top +
    geom_tippoint(aes(color = Genus), size = 1.5) +
    theme(legend.position = "right", legend.text = element_text(size = 7))
}

# ---- 保存树和图片 ----
write.tree(phy_tree(ps_top), file = file.path(OUTPUT_DIR, "genus_tree.nwk"))

ggsave(file.path(OUTPUT_DIR, "genus_tree.png"), tree_plot,
       width = 14, height = 10, dpi = 300)

cat("属水平系统发育树已完成\n")
