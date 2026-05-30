#!/usr/bin/env Rscript
# ============================================================
# SIMPER相似性百分比分析 (tool_id: amp-simper)
# 描述：使用SIMPER方法分析组间差异的贡献物种
#   计算每个物种对组间Bray-Curtis差异的平均贡献
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：simper_results.tsv, simper_barplot.png
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
if (!file.exists(meta_file)) stop("错误：找不到metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

# 相对丰度（SIMPER推荐使用）
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")
data_t <- t(rel_abund)  # 样本为行
grp <- factor(meta[[GROUP_COL]])

cat(sprintf("SIMPER分析：%d OTU，%d 样本，%d 组\n",
            ncol(data_t), nrow(data_t), length(levels(grp))))

# ---- SIMPER分析 ----
set.seed(42)
sim_res <- simper(data_t, grp, permutations = 999)

# ---- 提取所有成对比较结果 ----
all_results <- list()

for (comp_name in names(sim_res)) {
  sim_comp <- sim_res[[comp_name]]
  comp_groups <- strsplit(comp_name, "_")[[1]]

  # 构建结果数据框
  comp_df <- data.frame(
    Comparison = comp_name,
    OTU = rownames(sim_comp$average),
    Average_Contribution = round(sim_comp$average, 6),
    SD = round(sim_comp$sd, 6),
    Cumulative = round(sim_comp$cumsum, 4),
    P_value = signif(sim_comp$p, 4),
    stringsAsFactors = FALSE
  )
  all_results[[length(all_results) + 1]] <- comp_df
}

result_df <- do.call(rbind, all_results)
result_df <- result_df[order(result_df$Comparison, -result_df$Average_Contribution), ]

# ---- 输出结果 ----
write.table(result_df, file.path(OUTPUT_DIR, "simper_results.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

cat(sprintf("SIMPER完成：%d 组比较\n", length(names(sim_res))))

# ---- 绘制Top贡献物种柱状图 ----
# 取第一个比较的top15
first_comp <- result_df[result_df$Comparison == result_df$Comparison[1], ]
top_n <- min(15, nrow(first_comp))
plot_df <- first_comp[1:top_n, ]
plot_df$OTU <- factor(plot_df$OTU, levels = rev(plot_df$OTU))

p <- ggplot(plot_df, aes(x = OTU, y = Average_Contribution, fill = Cumulative)) +
  geom_bar(stat = "identity", width = 0.7) +
  scale_fill_gradient(low = "lightblue", high = "darkblue") +
  coord_flip() +
  theme_bw(base_size = 11) +
  labs(x = "", y = "Average Contribution to Dissimilarity",
       fill = "Cumulative %",
       title = paste0("SIMPER: Top Contributors (", plot_df$Comparison[1], ")")) +
  theme(plot.title = element_text(hjust = 0.5))

ggsave(file.path(OUTPUT_DIR, "simper_barplot.png"), p, width = 10, height = 7, dpi = 300)
cat("SIMPER柱状图已保存\n")
