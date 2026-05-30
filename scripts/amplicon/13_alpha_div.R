#!/usr/bin/env Rscript
# ============================================================
# Alpha多样性显著性检验 (tool_id: amp-alpha-div)
# 描述：对Alpha多样性指数进行组间显著性检验
#   支持Kruskal-Wallis、Wilcoxon、ANOVA等方法
# 输入：alpha_diversity.tsv, metadata.tsv
# 输出：alpha_div_test.tsv, alpha_div_boxplot.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "ggpubr", "dplyr", "tidyr")
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

# ---- 读取Alpha多样性数据 ----
alpha_file <- file.path(INPUT_DIR, "alpha_diversity.tsv")
if (!file.exists(alpha_file)) stop("错误：找不到alpha_diversity.tsv，请先运行10_alpha_data.R")

alpha_df <- read.table(alpha_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
cat(sprintf("读取Alpha多样性数据：%d 样本\n", nrow(alpha_df)))

# ---- 检查分组列 ----
if (!GROUP_COL %in% colnames(alpha_df)) {
  stop(sprintf("错误：数据中未找到分组列 '%s'\n", GROUP_COL))
}

# ---- 定义要检验的多样性指标 ----
metrics <- c("Shannon", "Simpson", "Chao1", "ACE", "Richness", "Pielou")
metrics <- intersect(metrics, colnames(alpha_df))
if (length(metrics) == 0) stop("错误：未找到任何多样性指标列")

groups <- unique(alpha_df[[GROUP_COL]])
n_groups <- length(groups)
cat(sprintf("分组列：%s，共 %d 组：%s\n", GROUP_COL, n_groups, paste(groups, collapse = ", ")))

# ---- 对每个指标进行检验 ----
results <- list()

for (metric in metrics) {
  vals <- alpha_df[[metric]]
  grp <- alpha_df[[GROUP_COL]]

  # 根据分组数选择检验方法
  if (n_groups == 2) {
    # 两组：Wilcoxon秩和检验
    test_res <- wilcox.test(vals[grp == groups[1]], vals[grp == groups[2]], exact = FALSE)
    results[[metric]] <- data.frame(
      Metric = metric, Method = "Wilcoxon",
      Group1 = groups[1], Group2 = groups[2],
      Statistic = round(test_res$statistic, 4),
      P_value = signif(test_res$p.value, 4),
      Significance = ifelse(test_res$p.value < 0.05, "*", "ns"),
      stringsAsFactors = FALSE
    )
  } else {
    # 多组：Kruskal-Wallis检验
    test_res <- kruskal.test(vals, grp)
    results[[metric]] <- data.frame(
      Metric = metric, Method = "Kruskal-Wallis",
      Group1 = "All", Group2 = NA,
      Statistic = round(test_res$statistic, 4),
      P_value = signif(test_res$p.value, 4),
      Significance = ifelse(test_res$p.value < 0.05, "*", "ns"),
      stringsAsFactors = FALSE
    )
  }
}

result_df <- do.call(rbind, results)

# ---- 输出检验结果 ----
out_file <- file.path(OUTPUT_DIR, "alpha_div_test.tsv")
write.table(result_df, out_file, sep = "\t", quote = FALSE, row.names = FALSE)
cat(sprintf("显著性检验结果已保存：%s\n", out_file))

# ---- 绘制箱线图 ----
alpha_long <- alpha_df[, c("Sample", GROUP_COL, metrics)] %>%
  pivot_longer(cols = all_of(metrics), names_to = "Metric", values_to = "Value")

p <- ggplot(alpha_long, aes(x = !!sym(GROUP_COL), y = Value, fill = !!sym(GROUP_COL))) +
  geom_boxplot(outlier.shape = 21, width = 0.6, alpha = 0.7) +
  geom_jitter(width = 0.15, size = 1, alpha = 0.5) +
  facet_wrap(~Metric, scales = "free_y", ncol = 3) +
  theme_bw(base_size = 12) +
  labs(x = "", y = "Diversity Index", fill = GROUP_COL,
       title = "Alpha Diversity Comparison") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        plot.title = element_text(hjust = 0.5))

fig_file <- file.path(OUTPUT_DIR, "alpha_div_boxplot.png")
ggsave(fig_file, p, width = 12, height = 8, dpi = 300)
cat(sprintf("箱线图已保存：%s\n", fig_file))
