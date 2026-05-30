#!/usr/bin/env Rscript
# ============================================================
# DCA去趋势对应分析 (tool_id: amp-dca)
# 描述：进行DCA分析确定数据梯度长度，指导后续分析方法选择
#   梯度长度>4用单峰模型(CA/NMDS)，<3用线性模型(PCA/RDA)
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：dca_plot.png, dca_data.tsv, dca_summary.txt
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
if (!file.exists(meta_file)) stop("错误：DCA需要metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

cat(sprintf("DCA分析：%d OTU，%d 样本\n", nrow(otu_mat), ncol(otu_mat)))

# ---- DCA分析 ----
dca_res <- decorana(t(otu_mat))

# 输出DCA摘要
summary_text <- capture.output(summary(dca_res))
cat("DCA摘要：\n")
cat(summary_text, sep = "\n")

# 提取梯度长度
eig_vals <- dca_res$evals
axis_lengths <- dca_res$adiff
gradient_length <- axis_lengths[1]

cat(sprintf("\n第一轴梯度长度：%.2f\n", gradient_length))

# ---- 分析建议 ----
if (gradient_length > 4) {
  suggestion <- "梯度长度 > 4：建议使用单峰模型（CA, DCA, NMDS, CCA）"
} else if (gradient_length < 3) {
  suggestion <- "梯度长度 < 3：建议使用线性模型（PCA, RDA）"
} else {
  suggestion <- "梯度长度 3-4：两种模型均可，推荐NMDS"
}
cat(suggestion, "\n")

# ---- 保存DCA摘要 ----
writeLines(c(
  "DCA分析报告",
  "============",
  sprintf("OTU数：%d", nrow(otu_mat)),
  sprintf("样本数：%d", ncol(otu_mat)),
  "",
  sprintf("第一轴梯度长度：%.2f", gradient_length),
  sprintf("分析建议：%s", suggestion),
  "",
  "DCA详细摘要：",
  summary_text
), file.path(OUTPUT_DIR, "dca_summary.txt"))

# ---- 提取DCA坐标 ----
dca_sites <- as.data.frame(scores(dca_res, display = "sites", choices = 1:2))
colnames(dca_sites) <- c("DCA1", "DCA2")
dca_sites$Sample <- rownames(dca_sites)
dca_sites[[GROUP_COL]] <- meta[[GROUP_COL]][match(dca_sites$Sample, meta$Sample)]

write.table(dca_sites, file.path(OUTPUT_DIR, "dca_data.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# ---- 绘制DCA散点图 ----
n_grp <- length(unique(dca_sites[[GROUP_COL]]))
color_palette <- if (n_grp <= 8) {
  RColorBrewer::brewer.pal(max(3, n_grp), "Set1")[1:n_grp]
} else {
  rainbow(n_grp)
}

p <- ggplot(dca_sites, aes(x = DCA1, y = DCA2,
                             color = !!sym(GROUP_COL), fill = !!sym(GROUP_COL))) +
  stat_ellipse(geom = "polygon", alpha = 0.15, level = 0.95) +
  geom_point(size = 3.5, alpha = 0.85, shape = 21, color = "black", stroke = 0.3) +
  scale_fill_manual(values = color_palette) +
  scale_color_manual(values = color_palette) +
  theme_bw(base_size = 13) +
  labs(x = sprintf("DCA1 (gradient=%.2f)", gradient_length),
       y = "DCA2",
       title = sprintf("DCA - Detrended Correspondence Analysis")) +
  annotate("text", x = Inf, y = -Inf, hjust = 1.1, vjust = -0.5,
           label = suggestion, size = 3.5, color = "grey30") +
  theme(plot.title = element_text(hjust = 0.5, size = 15),
        legend.position = "right")

ggsave(file.path(OUTPUT_DIR, "dca_plot.png"), p, width = 10, height = 8, dpi = 300)
cat("DCA分析完成\n")
