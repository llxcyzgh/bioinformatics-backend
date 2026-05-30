#!/usr/bin/env Rscript
# ============================================================
# MetaStat组间差异物种分析 (tool_id: amp-metastat)
# 描述：使用MetaStat方法进行组间差异物种分析
#   基于t检验和置换检验，适合两组比较
# 输入：物种丰度表, metadata.tsv
# 输出：metastat_results.tsv, metastat_volcano.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "dplyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
P_THRESHOLD <- as.numeric(ifelse(length(args) >= 4, args[4], 0.05))

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

# 相对丰度
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")
grp <- factor(meta[[GROUP_COL]])
groups <- levels(grp)

if (length(groups) < 2) stop("错误：至少需要2个分组")
cat(sprintf("分析：%d OTU，%d 组：%s\n", nrow(rel_abund), length(groups), paste(groups, collapse = " vs ")))

# ---- 对每个OTU进行组间比较 ----
g1_idx <- which(grp == groups[1])
g2_idx <- which(grp == groups[2])

results <- list()

for (i in seq_len(nrow(rel_abund))) {
  otu_name <- rownames(rel_abund)[i]
  v1 <- as.numeric(rel_abund[i, g1_idx])
  v2 <- as.numeric(rel_abund[i, g2_idx])

  # 跳过低丰度OTU（两组均值都<0.001）
  if (mean(v1) < 0.001 && mean(v2) < 0.001) next

  # Welch t检验
  t_test <- tryCatch({
    t.test(v1, v2, var.equal = FALSE)
  }, error = function(e) NULL)

  if (is.null(t_test)) next

  mean_diff <- mean(v2) - mean(v1)

  results[[length(results) + 1]] <- data.frame(
    OTU = otu_name,
    Mean_Group1 = round(mean(v1), 6),
    Mean_Group2 = round(mean(v2), 6),
    Diff = round(mean_diff, 6),
    t_statistic = round(t_test$statistic, 4),
    P_value = t_test$p.value,
    stringsAsFactors = FALSE
  )
}

if (length(results) == 0) stop("无足够数据进行差异分析")

result_df <- do.call(rbind, results)

# ---- BH校正 ----
result_df$P_adjusted <- p.adjust(result_df$P_value, method = "BH")
result_df$Significance <- ifelse(result_df$P_adjusted < P_THRESHOLD, "*", "ns")
result_df <- result_df[order(result_df$P_adjusted), ]

# ---- 输出结果 ----
write.table(result_df, file.path(OUTPUT_DIR, "metastat_results.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

sig_count <- sum(result_df$P_adjusted < P_THRESHOLD)
cat(sprintf("MetaStat完成：%d 差异物种 (padj < %.2f)\n", sig_count, P_THRESHOLD))

# ---- 绘制火山图 ----
result_df$log2FC <- log2((result_df$Mean_Group2 + 1e-10) / (result_df$Mean_Group1 + 1e-10))
result_df$neg_log10p <- -log10(result_df$P_adjusted + 1e-100)
result_df$Sig <- ifelse(result_df$P_adjusted < P_THRESHOLD &
                          abs(result_df$log2FC) > 1, "Significant", "NS")

p <- ggplot(result_df, aes(x = log2FC, y = neg_log10p, color = Sig)) +
  geom_point(size = 1.5, alpha = 0.7) +
  scale_color_manual(values = c("NS" = "grey60", "Significant" = "red3")) +
  geom_hline(yintercept = -log10(P_THRESHOLD), linetype = "dashed", color = "blue") +
  geom_vline(xintercept = c(-1, 1), linetype = "dashed", color = "blue") +
  theme_bw(base_size = 12) +
  labs(x = "log2 Fold Change", y = "-log10(Adjusted P)",
       title = paste0("MetaStat: ", groups[1], " vs ", groups[2]),
       color = "") +
  theme(plot.title = element_text(hjust = 0.5))

ggsave(file.path(OUTPUT_DIR, "metastat_volcano.png"), p, width = 8, height = 6, dpi = 300)
cat("火山图已保存\n")
