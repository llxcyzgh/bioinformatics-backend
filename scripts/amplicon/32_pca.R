#!/usr/bin/env Rscript
# ============================================================
# PCA主成分分析 (tool_id: amp-pca)
# 描述：对物种丰度数据进行PCA主成分分析并绘制散点图
#   基于Hellinger转化后的OTU表
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：pca_plot.png, pca_data.tsv, pca_eigenvalues.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("vegan", "ggplot2", "dplyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")
if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(meta_file)) stop("错误：PCA需要metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

cat(sprintf("PCA分析：%d OTU，%d 样本\n", nrow(otu_mat), ncol(otu_mat)))

# ---- Hellinger转化（推荐用于PCA）----
otu_hell <- decostand(t(otu_mat), method = "hellinger")

# ---- PCA分析 ----
pca_res <- rda(otu_hell)
pca_summary <- summary(pca_res)

# 提取样本坐标
scores_sites <- scores(pca_res, display = "sites", choices = 1:2)
pca_df <- as.data.frame(scores_sites)
colnames(pca_df) <- c("PC1", "PC2")
pca_df$Sample <- rownames(pca_df)
pca_df[[GROUP_COL]] <- meta[[GROUP_COL]][match(pca_df$Sample, meta$Sample)]

# 方差解释率
eig <- eigenvals(pca_res)
var_exp <- eig / sum(eig) * 100
pc1_var <- round(var_exp[1], 2)
pc2_var <- round(var_exp[2], 2)

cat(sprintf("PC1: %.2f%%, PC2: %.2f%%\n", pc1_var, pc2_var))

# ---- 保存PCA数据 ----
write.table(pca_df, file.path(OUTPUT_DIR, "pca_data.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

eig_df <- data.frame(
  PC = paste0("PC", seq_along(eig)),
  Eigenvalue = round(as.numeric(eig), 4),
  Variance_Explained = round(as.numeric(var_exp), 2),
  Cumulative = round(cumsum(as.numeric(var_exp)), 2),
  stringsAsFactors = FALSE
)
write.table(eig_df, file.path(OUTPUT_DIR, "pca_eigenvalues.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# ---- 绘制PCA散点图 ----
n_grp <- length(unique(pca_df[[GROUP_COL]]))
color_palette <- if (n_grp <= 8) {
  RColorBrewer::brewer.pal(max(3, n_grp), "Set1")[1:n_grp]
} else {
  rainbow(n_grp)
}

p <- ggplot(pca_df, aes(x = PC1, y = PC2, color = !!sym(GROUP_COL), fill = !!sym(GROUP_COL))) +
  stat_ellipse(geom = "polygon", alpha = 0.15, level = 0.95) +
  geom_point(size = 3, alpha = 0.8, shape = 21, color = "black", stroke = 0.3) +
  scale_fill_manual(values = color_palette) +
  scale_color_manual(values = color_palette) +
  theme_bw(base_size = 13) +
  labs(x = sprintf("PC1 (%.2f%%)", pc1_var),
       y = sprintf("PC2 (%.2f%%)", pc2_var),
       title = "PCA - Principal Component Analysis") +
  theme(plot.title = element_text(hjust = 0.5, size = 15),
        legend.position = "right")

ggsave(file.path(OUTPUT_DIR, "pca_plot.png"), p, width = 10, height = 8, dpi = 300)
cat("PCA分析完成\n")
