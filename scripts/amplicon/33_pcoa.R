#!/usr/bin/env Rscript
# ============================================================
# PCoA主坐标分析 (tool_id: amp-pcoa)
# 描述：基于Beta多样性距离矩阵进行PCoA分析
#   支持Bray-Curtis, Jaccard, UniFrac等距离
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：pcoa_plot.png, pcoa_data.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("vegan", "ape", "ggplot2", "dplyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR   <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR  <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL   <- ifelse(length(args) >= 3, args[3], "Group")
DIST_METHOD <- ifelse(length(args) >= 4, args[4], "bray")

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")
if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(meta_file)) stop("错误：PCoA需要metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

cat(sprintf("PCoA分析：%d OTU，%d 样本，距离方法：%s\n",
            nrow(otu_mat), ncol(otu_mat), DIST_METHOD))

# ---- 计算距离矩阵 ----
dist_mat <- vegdist(t(otu_mat), method = DIST_METHOD)

# ---- PCoA分析 ----
pcoa_res <- pcoa(dist_mat)

# 提取坐标
coords <- pcoa_res$vectors[, 1:2]
var_exp <- pcoa_res$values$Relative_eig[1:2] * 100
axis1_var <- round(var_exp[1], 2)
axis2_var <- round(var_exp[2], 2)

cat(sprintf("Axis1: %.2f%%, Axis2: %.2f%%\n", axis1_var, axis2_var))

# 构建绘图数据
pcoa_df <- as.data.frame(coords)
colnames(pcoa_df) <- c("Axis1", "Axis2")
pcoa_df$Sample <- rownames(pcoa_df)
pcoa_df[[GROUP_COL]] <- meta[[GROUP_COL]][match(pcoa_df$Sample, meta$Sample)]

# ---- 保存数据 ----
write.table(pcoa_df, file.path(OUTPUT_DIR, "pcoa_data.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# ---- 绘制PCoA散点图 ----
n_grp <- length(unique(pcoa_df[[GROUP_COL]]))
color_palette <- if (n_grp <= 8) {
  RColorBrewer::brewer.pal(max(3, n_grp), "Set1")[1:n_grp]
} else {
  rainbow(n_grp)
}

p <- ggplot(pcoa_df, aes(x = Axis1, y = Axis2,
                          color = !!sym(GROUP_COL), fill = !!sym(GROUP_COL))) +
  stat_ellipse(geom = "polygon", alpha = 0.15, level = 0.95) +
  geom_point(size = 3.5, alpha = 0.85, shape = 21, color = "black", stroke = 0.3) +
  scale_fill_manual(values = color_palette) +
  scale_color_manual(values = color_palette) +
  theme_bw(base_size = 13) +
  labs(x = sprintf("PCoA1 (%.2f%%)", axis1_var),
       y = sprintf("PCoA2 (%.2f%%)", axis2_var),
       title = sprintf("PCoA (%s distance)", toupper(DIST_METHOD))) +
  theme(plot.title = element_text(hjust = 0.5, size = 15),
        legend.position = "right")

ggsave(file.path(OUTPUT_DIR, "pcoa_plot.png"), p, width = 10, height = 8, dpi = 300)
cat("PCoA分析完成\n")
