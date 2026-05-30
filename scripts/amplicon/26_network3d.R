#!/usr/bin/env Rscript
# ============================================================
# 3D微生物网络可视化 (tool_id: amp-network3d)
# 描述：基于物种丰度相关性构建3D微生物共发生网络
#   生成可交互的3D网络HTML文件
# 输入：network_edges.tsv, network_nodes.tsv（或OTU表）
# 输出：network_3d.html, network_3d.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("igraph", "ggplot2", "dplyr", "Hmisc")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# 尝试加载3D可视化包
has_threejs <- requireNamespace("threejs", quietly = TRUE)
has_rgl <- requireNamespace("rgl", quietly = TRUE)

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR    <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR   <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
COR_THRESHOLD <- as.numeric(ifelse(length(args) >= 3, args[3], 0.6))

if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR, recursive = TRUE)

# ---- 尝试读取已有网络或从OTU表构建 ----
edges_file <- file.path(INPUT_DIR, "network_edges.tsv")
nodes_file <- file.path(INPUT_DIR, "network_nodes.tsv")

if (file.exists(edges_file) && file.exists(nodes_file)) {
  edges_df <- read.table(edges_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
  nodes_df <- read.table(nodes_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)
  cat("读取已有网络数据\n")
} else {
  # 从OTU表构建网络
  otu_file <- file.path(INPUT_DIR, "otu.tsv")
  if (!file.exists(otu_file)) stop("错误：找不到OTU表或网络数据文件")

  otu_mat <- as.matrix(read.table(otu_file, header = TRUE, row.names = 1, sep = "\t",
                                   check.names = FALSE))
  otu_mat <- otu_mat[rowSums(otu_mat) > 0, , drop = FALSE]
  prevalence <- rowSums(otu_mat > 0) / ncol(otu_mat)
  otu_mat <- otu_mat[prevalence >= 0.2, , drop = FALSE]

  rel_abund <- sweep(otu_mat, 2, colSums(otu_mat), "/")
  if (nrow(rel_abund) > 150) {
    rel_abund <- rel_abund[order(rowMeans(rel_abund), decreasing = TRUE)[1:150], ]
  }

  cor_res <- rcorr(t(rel_abund), type = "spearman")
  cor_mat <- cor_res$r
  p_mat <- cor_res$P
  diag(cor_mat) <- 0; diag(p_mat) <- 1
  sig_mask <- (abs(cor_mat) >= COR_THRESHOLD) & (p_mat < 0.05)
  cor_mat[!sig_mask] <- 0

  g <- graph_from_adjacency_matrix(cor_mat, mode = "undirected", weighted = TRUE, diag = FALSE)
  deg <- degree(g)
  cluster_info <- cluster_louvain(g)

  nodes_df <- data.frame(OTU = V(g)$name, Degree = deg,
                          Module = membership(cluster_info),
                          stringsAsFactors = FALSE)
  edges_df <- as_data_frame(g, what = "edges")
  colnames(edges_df) <- c("Source", "Target", "Weight")
  cat(sprintf("构建网络：%d 节点，%d 边\n", nrow(nodes_df), nrow(edges_df)))
}

# ---- 构建igraph对象 ----
if (!"OTU" %in% colnames(nodes_df)) {
  colnames(nodes_df)[1] <- "OTU"
}
g <- graph_from_data_frame(edges_df, vertices = nodes_df, directed = FALSE)

# ---- 3D布局 ----
set.seed(42)
layout_3d <- layout_with_fr(g, dim = 3)

# ---- 使用rgl生成3D图 ----
if (has_rgl) {
  library(rgl)
  # 按模块着色
  if ("Module" %in% colnames(nodes_df)) {
    colors <- rainbow(max(nodes_df$Module))[nodes_df$Module]
  } else {
    colors <- rep("steelblue", vcount(g))
  }

  sizes <- if ("Degree" %in% colnames(nodes_df)) {
    log2(nodes_df$Degree + 1) * 5
  } else {
    rep(5, vcount(g))
  }

  # 边颜色
  edge_colors <- if ("Weight" %in% colnames(edges_df)) {
    ifelse(edges_df$Weight > 0, "red", "blue")
  } else {
    rep("grey50", ecount(g))
  }

  open3d()
  plot3d(layout_3d[, 1], layout_3d[, 2], layout_3d[, 3],
         type = "s", size = sizes, color = colors,
         xlab = "", ylab = "", zlab = "", axes = FALSE,
         main = "3D Microbial Network")

  # 绘制边
  edge_list <- as_edgelist(g)
  for (i in seq_len(nrow(edge_list))) {
    idx1 <- which(V(g)$name == edge_list[i, 1])
    idx2 <- which(V(g)$name == edge_list[i, 2])
    lines3d(layout_3d[c(idx1, idx2), 1],
            layout_3d[c(idx1, idx2), 2],
            layout_3d[c(idx1, idx2), 3],
            color = edge_colors[i], alpha = 0.3)
  }

  # 保存快照
  snapshot3d(file.path(OUTPUT_DIR, "network_3d.png"))
  # 保存HTML
  htmlwidgets::saveWidget(rglwidget(), file.path(OUTPUT_DIR, "network_3d.html"))
  cat("3D网络HTML已保存\n")
  close3d()
} else {
  cat("提示：安装rgl包可获得3D交互网络 (install.packages('rgl'))\n")

  # 回退：保存3D坐标数据
  coord_df <- data.frame(
    OTU = V(g)$name,
    X = layout_3d[, 1], Y = layout_3d[, 2], Z = layout_3d[, 3]
  )
  write.table(coord_df, file.path(OUTPUT_DIR, "network_3d_coords.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
  cat("3D坐标数据已保存（未安装rgl）\n")
}

cat("3D网络可视化完成\n")
