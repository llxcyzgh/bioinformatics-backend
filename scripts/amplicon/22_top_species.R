#!/usr/bin/env Rscript
# ============================================================
# Top10优势物种柱状图 (tool_id: amp-top-species)
# 描述：绘制各组Top10优势物种的相对丰度堆叠柱状图
# 输入：OTU/物种丰度表 (otu.tsv), taxonomy.tsv, metadata.tsv
# 输出：top_species_barplot.png, top_species_abundance.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "dplyr", "tidyr", "phyloseq")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
TAXA_LEVEL <- ifelse(length(args) >= 4, args[4], "Genus")
TOP_N      <- as.integer(ifelse(length(args) >= 5, args[5], 10))

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
tax_file <- file.path(INPUT_DIR, "taxonomy.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

# ---- 聚合到分类水平 ----
if (file.exists(tax_file)) {
  tax_df <- read.table(tax_file, header = TRUE, row.names = 1, sep = "\t",
                        stringsAsFactors = FALSE, comment.char = "")
  if (TAXA_LEVEL %in% colnames(tax_df)) {
    taxa_assignments <- tax_df[[TAXA_LEVEL]]
    taxa_assignments[is.na(taxa_assignments)] <- "Unclassified"
    otu_mat <- rowsum(otu_mat, group = taxa_assignments)
    cat(sprintf("按 %s 水平聚合：%d 分类单元\n", TAXA_LEVEL, nrow(otu_mat)))
  }
}

# 相对丰度
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")

# ---- 筛选Top N物种 ----
mean_abund <- rowMeans(rel_abund)
top_taxa <- names(sort(mean_abund, decreasing = TRUE))[1:min(TOP_N, nrow(rel_abund))]

# 其他物种合并为"Others"
top_mat <- rel_abund[top_taxa, , drop = FALSE]
others <- colSums(rel_abund[!rownames(rel_abund) %in% top_taxa, , drop = FALSE])
top_mat <- rbind(top_mat, Others = others)

cat(sprintf("Top %d 物种占总丰度 %.1f%%\n",
            TOP_N, sum(mean_abund[top_taxa]) * 100))

# ---- 读取metadata ----
meta <- NULL
if (file.exists(meta_file)) {
  meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
}

# ---- 整理绘图数据 ----
plot_df <- as.data.frame(t(top_mat))
plot_df$Sample <- rownames(plot_df)

if (!is.null(meta) && "Sample" %in% colnames(meta)) {
  plot_df <- merge(plot_df, meta[, c("Sample", GROUP_COL)], by = "Sample", all.x = TRUE)
}

plot_long <- plot_df %>%
  pivot_longer(cols = -c(Sample, !!sym(GROUP_COL)),
               names_to = "Taxa", values_to = "Abundance")

# ---- 绘制堆叠柱状图 ----
n_colors <- length(top_taxa) + 1
color_palette <- c(RColorBrewer::brewer.pal(min(n_colors, 12), "Set3"),
                   rep("grey80", max(0, n_colors - 12)))

if (!is.null(meta) && GROUP_COL %in% colnames(plot_df)) {
  # 按组绘制
  group_mean <- plot_long %>%
    group_by(!!sym(GROUP_COL), Taxa) %>%
    summarise(Abundance = mean(Abundance), .groups = "drop")

  p <- ggplot(group_mean, aes(x = !!sym(GROUP_COL), y = Abundance, fill = Taxa)) +
    geom_bar(stat = "identity", width = 0.8) +
    scale_fill_manual(values = color_palette) +
    theme_bw(base_size = 12)
} else {
  p <- ggplot(plot_long, aes(x = Sample, y = Abundance, fill = Taxa)) +
    geom_bar(stat = "identity", width = 0.8) +
    scale_fill_manual(values = color_palette) +
    theme_bw(base_size = 10) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))
}

p <- p + labs(x = "", y = "Relative Abundance", fill = TAXA_LEVEL,
              title = paste0("Top ", TOP_N, " Dominant Taxa")) +
  theme(plot.title = element_text(hjust = 0.5))

ggsave(file.path(OUTPUT_DIR, "top_species_barplot.png"), p, width = 12, height = 7, dpi = 300)

# ---- 保存丰度表 ----
write.table(round(as.data.frame(t(top_mat)), 6),
            file.path(OUTPUT_DIR, "top_species_abundance.tsv"),
            sep = "\t", quote = FALSE)
cat(sprintf("Top物种分析完成，图片已保存\n"))
