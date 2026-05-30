#!/usr/bin/env Rscript
# ============================================================
# Alpha稀疏曲线 (tool_id: amp-alpha-rarefaction)
# 描述：绘制Alpha多样性稀疏曲线，评估测序深度是否足够
# 输入：OTU表 (otu.tsv)，可选metadata
# 输出：rarefaction_curve.png, rarefaction_data.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("vegan", "ggplot2", "dplyr", "tidyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
STEP_SIZE  <- as.integer(ifelse(length(args) >= 3, args[3], 100))

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取OTU表 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
if (!file.exists(otu_file)) stop("错误：找不到OTU表文件 otu.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE, comment.char = ""))
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

cat(sprintf("OTU表：%d OTU，%d 样本\n", nrow(otu_mat), ncol(otu_mat)))

# ---- 计算稀疏曲线 ----
# 转置为样本xOTU格式
otu_t <- t(otu_mat)
min_depth <- min(rowSums(otu_t))
max_depth <- max(rowSums(otu_t))

cat(sprintf("最小测序深度：%d，最大测序深度：%d\n", min_depth, max_depth))

# 使用vegan的rarecurve函数
set.seed(42)
rare_out <- rarecurve(otu_t, step = STEP_SIZE, sample = min_depth,
                       tidy = TRUE, label = FALSE)

colnames(rare_out) <- c("Sample", "Depth", "Species")

# ---- 读取分组信息 ----
meta <- NULL
meta_file <- file.path(INPUT_DIR, "metadata.tsv")
if (file.exists(meta_file)) {
  meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
  rare_out <- merge(rare_out, meta, by = "Sample", all.x = TRUE)
}

# ---- 保存稀疏数据 ----
data_file <- file.path(OUTPUT_DIR, "rarefaction_data.tsv")
write.table(rare_out, data_file, sep = "\t", quote = FALSE, row.names = FALSE)
cat(sprintf("稀疏数据已保存：%s\n", data_file))

# ---- 绘制稀疏曲线 ----
p <- ggplot(rare_out, aes(x = Depth, y = Species, group = Sample))

if (!is.null(meta) && "Group" %in% colnames(rare_out)) {
  p <- p + aes(color = Group) +
    scale_color_brewer(palette = "Set1")
} else {
  p <- p + aes(color = Sample) +
    guides(color = "none")
}

p <- p +
  geom_line(linewidth = 0.6, alpha = 0.8) +
  theme_bw(base_size = 12) +
  labs(x = "Sequencing Depth", y = "Observed OTU/ASV",
       title = "Rarefaction Curve") +
  theme(plot.title = element_text(hjust = 0.5, size = 14),
        legend.position = "right")

fig_file <- file.path(OUTPUT_DIR, "rarefaction_curve.png")
ggsave(fig_file, p, width = 10, height = 7, dpi = 300)
cat(sprintf("稀疏曲线图已保存：%s\n", fig_file))
