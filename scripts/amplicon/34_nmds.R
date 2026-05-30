#!/usr/bin/env Rscript
# ============================================================
# NMDS非度量多维标度 (tool_id: amp-nmds)
# 描述：基于Beta多样性距离矩阵进行NMDS排序分析
#   使用metaMDS自动选择最佳维度
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：nmds_plot.png, nmds_data.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("vegan", "ggplot2", "dplyr")
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
if (!file.exists(meta_file)) stop("错误：NMDS需要metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

cat(sprintf("NMDS分析：%d OTU，%d 样本，距离：%s\n",
            nrow(otu_mat), ncol(otu_mat), DIST_METHOD))

# ---- NMDS分析 ----
set.seed(42)
nmds_res <- metaMDS(t(otu_mat), distance = DIST_METHOD, k = 2,
                     trymax = 200, trace = 0, autotransform = TRUE)

stress_val <- nmds_res$stress
cat(sprintf("NMDS stress值：%.4f\n", stress_val))

if (stress_val > 0.2) {
  cat("警告：stress > 0.2，排序结果可能不可靠\n")
} else if (stress_val < 0.1) {
  cat("信息：stress < 0.1，排序结果良好\n")
}

# ---- 提取坐标 ----
nmds_points <- as.data.frame(nmds_res$points)
colnames(nmds_points) <- c("NMDS1", "NMDS2")
nmds_points$Sample <- rownames(nmds_points)
nmds_points[[GROUP_COL]] <- meta[[GROUP_COL]][match(nmds_points$Sample, meta$Sample)]

# ---- 保存数据 ----
write.table(nmds_points, file.path(OUTPUT_DIR, "nmds_data.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# ---- 绘制NMDS散点图 ----
n_grp <- length(unique(nmds_points[[GROUP_COL]]))
color_palette <- if (n_grp <= 8) {
  RColorBrewer::brewer.pal(max(3, n_grp), "Set1")[1:n_grp]
} else {
  rainbow(n_grp)
}

p <- ggplot(nmds_points, aes(x = NMDS1, y = NMDS2,
                               color = !!sym(GROUP_COL), fill = !!sym(GROUP_COL))) +
  stat_ellipse(geom = "polygon", alpha = 0.15, level = 0.95) +
  geom_point(size = 3.5, alpha = 0.85, shape = 21, color = "black", stroke = 0.3) +
  scale_fill_manual(values = color_palette) +
  scale_color_manual(values = color_palette) +
  theme_bw(base_size = 13) +
  labs(x = "NMDS1", y = "NMDS2",
       title = sprintf("NMDS (%s, stress=%.4f)", toupper(DIST_METHOD), stress_val)) +
  theme(plot.title = element_text(hjust = 0.5, size = 15),
        legend.position = "right")

ggsave(file.path(OUTPUT_DIR, "nmds_plot.png"), p, width = 10, height = 8, dpi = 300)
cat("NMDS分析完成\n")
