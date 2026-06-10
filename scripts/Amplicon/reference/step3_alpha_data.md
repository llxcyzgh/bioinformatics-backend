# Alpha Data - Alpha 多样性指数计算模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | alpha_data |
| **Description** | Alpha 多样性指数计算与稀化曲线分析，评估样本内物种多样性 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组多样性分析 |
| **估算机时** | 1.0 小时 |
| **报价分数** | 1.8 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|------|
| asv_table.even.txt | 均一化 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_alpha_data/asv_table.even.txt) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| alpha_index_table/alpha_diversity_index.txt | 综合 Alpha 指数表 | TXT | 16S/18S/ITS | 通用 | - |
| alpha_index_table/*.qza | Alpha 多样性指数 | QZA | 16S/18S/ITS | 通用 | - |
| alpha_rarefaction.qzv | Alpha 稀化曲线可视化 | QZV | 16S/18S/ITS | 通用 | - |

---


## 执行命令


**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_alpha_data.sh -i asv_table.even.txt [-t rooted-tree.qza] [-m alpha.mf]
# 输出：alpha_index_table/*.qza, alpha_diversity_index.txt, alpha_rarefaction.qzv
```

**示例 1**：仅计算 Alpha 指数
```bash
bash ${AMPLICON_ROOT}/scripts/step3_alpha_data.sh -i asv_table.even.txt
# 输出：alpha_index_table/chao1.qza, alpha_index_table/shannon.qza, ..., alpha_diversity_index.txt
```

**示例 2**：计算 Alpha 指数 + 稀化曲线
```bash
bash ${AMPLICON_ROOT}/scripts/step3_alpha_data.sh -i asv_table.even.txt -t rooted-tree.qza -m alpha.mf
# 输出：alpha_index_table/*.qza, alpha_diversity_index.txt, alpha_rarefaction.qzv
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 均一化 ASV 表路径 | 是 | - | asv_table.even.txt |
| -t, --tree | 有根系统发育树路径 | 否 | - | rooted-tree.qza |
| -m, --meta | 样本元数据文件路径 | 否 | - | alpha.mf |

---

## Alpha 多样性指数

| 指数 | 描述 | 生态学意义 |
|------|------|-----------|
| **chao1** | Chao1 丰富度估计 | 估计样本中物种总数 |
| **shannon** | Shannon 多样性指数 | 综合考虑物种丰富度和均匀度 |
| **simpson** | Simpson 多样性指数 | 优势物种的 dominance |
| **observed_features** | 观测物种数 | 实际检测到的 ASV 数量 |
| **goods_coverage** | Goods 覆盖度 | 测序深度是否足够 |
| **dominance** | Simpson 优势度 | 优势物种的支配程度 |
| **pielou_e** | Pielou 均匀度 | 物种分布的均匀程度 |

---

## 流程步骤

```
1️⃣ BIOM 转换 (asv_table.even.txt → asv_table.even.biom)
   ↓
2️⃣ 导入 QIIME2 (asv_table.even.biom → asv_table.even.qza)
   ↓
3️⃣ 计算 Alpha 指数 (7 个指数：chao1, shannon, simpson, ...)
   ↓
4️⃣ 导出指数表 (合并为 alpha_diversity_index.txt)
   ↓
5️⃣ Alpha 稀化曲线（如果有 tree 和 meta）
```

---

## alpha_diversity_index.txt 格式

```
Sample_Name	chao1	dominance	goods_coverage	observed_features	pielou_e	shannon	simpson
Sample001	125.3	0.15	0.98	120	0.85	3.21	0.85
Sample002	98.7	0.22	0.96	95	0.78	2.85	0.78
...
```

---
## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **conda**: `/software/anaconda3/bin/conda`
- **qiime**: `/software/anaconda3/envs/16s-env/bin/qiime`
- **biom**: `/software/anaconda3/envs/16s-env/bin/biom`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CONDA_BIN="/your/path/to/conda"' > .env
echo 'export QIIME_BIN="/your/path/to/qiime"' >> .env
echo 'export BIOM_BIN="/your/path/to/biom"' >> .env
source .env
bash step3_alpha_data.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt | 均一化 ASV 表 |
| step3_phylogeny | rooted-tree.qza | 有根系统发育树 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step4_alpha | alpha_diversity_index.txt | Alpha 多样性统计检验 |
| step4_alpha_boxplot | alpha_diversity_index.txt | Alpha 指数箱线图 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step3_alpha_data.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step3_alpha_data.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step3_alpha_data/`

---

最后更新：2026-04-15
