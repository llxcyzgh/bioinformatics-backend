#!/usr/bin/env Rscript
# ============================================================
# 2D微生物共发生网络 (tool_id: amp-network)
# 描述：基于物种丰度相关性构建微生物共发生网络
#   使用Spearman/Pearson相关 + 随机矩阵理论筛选
# 输入：OTU表 (otu.tsv)
# 输出：network_edges.tsv, network_nodes.tsv, network_2d.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("ggplot2", "dplyr", "igraph", "Hmisc")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR    <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR   <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
COR_METHOD   <- ifelse(length(args) >= 3, args[3], "spearman")  # spearman, pearson
COR_THRESHOLD <- as.numeric(ifelse(length(args) >= 4, args[4], 0.6))
P_THRESHOLD  <- as.numeric(ifelse(length(args) >= 5, args[5], 0.05))

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 读取数据 ----
otu_file <- file.path(INPUT_DIR, "otu.tsv")
if (!file.exists(otu_file)) stop("错误：找不到OTU表 otu.tsv")

otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                 check.names = FALSE))
otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]

# 过滤低出现率OTU（出现在<20%样本中的去除）
prevalence <- rowSums(otu_mat > 0) / ncol(otu_mat)
otu_mat <- otu_mat[prevalence >= 0.2, , drop = FALSE]

# 相对丰度
rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")

# 只保留Top200高丰度OTU（避免网络过大）
if (nrow(rel_abund) > 200) {
  mean_abund <- rowMeans(rel_abund)
  rel_abund <- rel_abund[names(sort(mean_abund, decreasing = TRUE))[1:200], ]
}

n_taxa <- nrow(rel_abund)
cat(sprintf("网络分析：%d 个OTU，%d 个样本\n", n_taxa, ncol(rel_abund)))

# ---- 计算相关矩阵 ----
cat("计算相关矩阵...\n")
cor_res <- rcorr(t(rel_abund), type = COR_METHOD)
cor_mat <- cor_res$r
p_mat <- cor_res$P

# ---- 筛选显著相关边 ----
diag(cor_mat) <- 0
diag(p_mat) <- 1

# 应用阈值
sig_mask <- (abs(cor_mat) >= COR_THRESHOLD) & (p_mat < P_THRESHOLD)
cor_mat[!sig_mask] <- 0

n_edges <- sum(sig_mask) / 2  # 对称矩阵
cat(sprintf("显著相关边数：%d (|r| >= %.2f, p < %.3f)\n", n_edges, COR_THRESHOLD, P_THRESHOLD))

if (n_edges == 0) {
  cat("警告：未发现显著相关，尝试降低阈值\n")
  quit(status = 0)
}

# ---- 构建igraph网络 ----
adj_mat <- cor_mat
g <- graph_from_adjacency_matrix(adj_mat, mode = "undirected", weighted = TRUE, diag = FALSE)

# 计算网络拓扑参数
deg <- degree(g)
betw <- betweenness(g)
cluster_info <- cluster_louvain(g)

cat(sprintf("网络节点：%d，边：%d\n", vcount(g), ecount(g)))
cat(sprintf("模块数：%d\n", length(cluster_info)))

# ---- 节点信息 ----
nodes_df <- data.frame(
  OTU = V(g)$name,
  Degree = deg,
  Betweenness = round(betw, 2),
  Module = membership(cluster_info),
  Abundance = round(rowMeans(rel_abund[V(g)$name, ]), 6),
  stringsAsFactors = FALSE
)

# ---- 边信息 ----
edges_df <- as_data_frame(g, what = "edges")
colnames(edges_df) <- c("Source", "Target", "Weight")
edges_df$Weight <- round(edges_df$Weight, 4)
edges_df$Type <- ifelse(edges_df$Weight > 0, "Positive", "Negative")

# ---- 保存网络数据 ----
write.table(nodes_df, file.path(OUTPUT_DIR, "network_nodes.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)
write.table(edges_df, file.path(OUTPUT_DIR, "network_edges.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# ---- 绘制网络图 ----
set.seed(42)
layout_mat <- layout_with_fr(g)

V(g)$size <- log2(deg + 1) * 3
V(g)$color <- membership(cluster_info)
E(g)$color <- ifelse(E(g)$weight > 0, "red3", "steelblue")
E(g)$width <- abs(E(g)$weight) * 3

p <- ggnetwork::ggnetwork() # 回退到基础绘图
# 使用igraph基础绘图保存
png(file.path(OUTPUT_DIR, "network_2d.png"), width = 2000, height = 2000, res = 150)
par(mar = c(1, 1, 3, 1))
plot(g, layout = layout_mat,
     vertex.label = NA,
     vertex.size = V(g)$size,
     vertex.color = V(g)$color,
     edge.color = E(g)$color,
     edge.width = E(g)$width,
     main = "Microbial Co-occurrence Network (2D)")
legend("topright", legend = c("Positive", "Negative"),
       col = c("red3", "steelblue"), lty = 1, lwd = 2)
dev.off()

cat("2D网络图已保存\n")
