#!/usr/bin/env Rscript
# ============================================================
# 随机森林分类 (tool_id: amp-randomforest)
# 描述：使用随机森林算法进行微生物组样本分类
#   特征重要性排序 + 交叉验证
# 输入：OTU表 (otu.tsv), metadata.tsv
# 输出：rf_model.rds, rf_importance.tsv, rf_importance.png
# ============================================================

# ---- 加载依赖包 ----
pkg_list <- c("randomForest", "ggplot2", "dplyr", "caret")
for (pkg in pkg_list) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, repos = "https://cloud.r-project.org")
  library(pkg, character.only = TRUE)
}

# ---- 解析命令行参数 ----
args <- commandArgs(trailingOnly = TRUE)
INPUT_DIR  <- ifelse(length(args) >= 1, args[1], ".")
OUTPUT_DIR <- ifelse(length(args) >= 2, args[2], INPUT_DIR)
GROUP_COL  <- ifelse(length(args) >= 3, args[3], "Group")
NTREE      <- as.integer(ifelse(length(args) >= 4, args[4], 500))

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

# 筛选低方差特征（保留前500个高方差OTU）
variances <- apply(rel_abund, 1, var)
top_idx <- order(variances, decreasing = TRUE)[1:min(500, length(variances))]
rel_abund <- rel_abund[top_idx, ]

# 构建训练数据
train_data <- as.data.frame(t(rel_abund))
train_data$Group <- factor(meta[[GROUP_COL]][match(rownames(train_data), meta$Sample)])

cat(sprintf("随机森林分类：%d 特征，%d 样本，%d 组\n",
            ncol(train_data) - 1, nrow(train_data), length(levels(train_data$Group))))

# ---- 构建随机森林模型 ----
set.seed(42)
n_samples <- nrow(train_data)
n_groups <- length(levels(train_data$Group))

# 确定mtry参数
mtry_val <- floor(sqrt(ncol(train_data) - 1))

rf_model <- randomForest(
  Group ~ ., data = train_data,
  ntree = NTREE, mtry = mtry_val,
  importance = TRUE,
  proximity = TRUE
)

cat(sprintf("OOB错误率：%.2f%%\n", rf_model$err.rate[ntree(rf_model), "OOB"] * 100))

# ---- 保存模型 ----
saveRDS(rf_model, file.path(OUTPUT_DIR, "rf_model.rds"))

# ---- 提取特征重要性 ----
imp <- importance(rf_model)
imp_df <- as.data.frame(imp)
imp_df$OTU <- rownames(imp_df)
imp_df <- imp_df[order(imp_df$MeanDecreaseAccuracy, decreasing = TRUE), ]

# 保存top30
top_n <- min(30, nrow(imp_df))
write.table(imp_df[1:top_n, ], file.path(OUTPUT_DIR, "rf_importance.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# ---- 绘制重要性图 ----
plot_df <- imp_df[1:top_n, ]
plot_df$OTU <- factor(plot_df$OTU, levels = rev(plot_df$OTU))

p <- ggplot(plot_df, aes(x = OTU, y = MeanDecreaseAccuracy)) +
  geom_bar(stat = "identity", fill = "steelblue", width = 0.7) +
  coord_flip() +
  theme_bw(base_size = 11) +
  labs(x = "", y = "Mean Decrease Accuracy",
       title = sprintf("Random Forest Top %d Features (OOB=%.1f%%)",
                       top_n, rf_model$err.rate[ntree(rf_model), "OOB"] * 100)) +
  theme(plot.title = element_text(hjust = 0.5, size = 12))

ggsave(file.path(OUTPUT_DIR, "rf_importance.png"), p, width = 10, height = 8, dpi = 300)
cat("随机森林分析完成\n")
