#!/usr/bin/env Rscript
# ============================================================
# Venn图分析 (tool_id: amp-venn)
# 描述：绘制Venn图展示各组特有和共有的OTU/ASV
#   支持2-5组比较
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：venn_diagram.png, venn_data.tsv
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "VennDiagram", "dplyr")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
MIN_PREVALENCE <- as.numeric(ifelse(length(args) >= 4, args[4], 0))  # 最小出现次数

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
meta_file <- file.path(INPUT_DIR, "metadata.tsv")

if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")
if (!file.exists(meta_file)) stop("错误：Venn图需要metadata.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
meta <- read.table(meta_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

# 样本匹配
shared <- intersect(colnames(otu_mat), meta$Sample)
otu_mat <- otu_mat[, shared]
meta <- meta[match(shared, meta$Sample), ]

grp <- factor(meta[[GROUP_COL]])
groups <- levels(grp)
n_groups <- length(groups)

cat(sprintf("Venn图分析：%d OTU，%d 组\n", nrow(otu_mat), n_groups))

if (n_groups < 2) stop("错误：至少需要2个分组")
if (n_groups > 5) {
  cat(sprintf("警告：Venn图最多支持5组，仅使用前5组\n"))
  groups <- groups[1:5]
  n_groups <- 5
}

# ---- 获取每组的OTU集合 ----
otu_sets <- list()
for (g in groups) {
  idx <- which(grp == g)
  # 在该组中出现次数 >= MIN_PREVALENCE 的OTU
  group_counts <- rowSums(otu_mat[, idx, drop = FALSE] > 0)
  otu_sets[[g]] <- names(which(group_counts > MIN_PREVALENCE))
  cat(sprintf("  %s: %d OTU\n", g, length(otu_sets[[g]])))
}

# ---- 计算交集/差集统计 ----
# 使用Reduce计算共有和特有
if (n_groups == 2) {
  shared_otus <- intersect(otu_sets[[1]], otu_sets[[2]])
  unique_1 <- setdiff(otu_sets[[1]], otu_sets[[2]])
  unique_2 <- setdiff(otu_sets[[2]], otu_sets[[1]])
  cat(sprintf("共有：%d，%s特有：%d，%s特有：%d\n",
              length(shared_otus), groups[1], length(unique_1), groups[2], length(unique_2)))
}

# ---- 保存Venn数据 ----
all_otus <- unique(unlist(otu_sets))
venn_matrix <- sapply(groups, function(g) all_otus %in% otu_sets[[g]])
colnames(venn_matrix) <- groups
rownames(venn_matrix) <- all_otus
venn_df <- as.data.frame(venn_matrix) * 1
venn_df$OTU <- all_otus
write.table(venn_df, file.path(OUTPUT_DIR, "venn_data.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# ---- 绘制Venn图 ----
fig_file <- file.path(OUTPUT_DIR, "venn_diagram.png")

colors <- c("dodgerblue", "firebrick3", "green3", "orange", "purple")[1:n_groups]

png(fig_file, width = 2000, height = 1600, res = 150)

venn_res <- venn.diagram(
  x = otu_sets,
  filename = NULL,
  fill = colors,
  alpha = 0.5,
  cat.cex = 1.2,
  cex = 1.5,
  cat.fontface = "bold",
  margin = 0.1,
  main = "OTU/ASV Venn Diagram",
  main.cex = 1.8
)
grid.draw(venn_res)

dev.off()

cat(sprintf("Venn图已保存：%s\n", fig_file))

# ---- 输出交集OTU列表 ----
common_otus <- Reduce(intersect, otu_sets)
writeLines(common_otus, file.path(OUTPUT_DIR, "venn_common_otus.txt"))
cat(sprintf("共有OTU列表已保存（%d 个）\n", length(common_otus)))
