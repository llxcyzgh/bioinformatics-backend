# Genus Tree - 属水平物种进化树模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | genus_tree |
| **Description** | 基于属水平 Top100 优势物种构建进化树，展示优势菌属的系统发育关系与丰度分布 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组优势物种进化分析 |
| **估算机时** | 2.0 小时 |
| **报价分数** | 3.6 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| all_tax_assignments.txt | 物种注释表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_genus_tree/all_tax_assignments.txt) |
| asv_table.g.relative.xls | 属水平相对丰度表（样本） | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_genus_tree/asv_table.g.relative.xls) |
| asv_table.relative.xls | 样本相对丰度表（select_OTUs 用） | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_genus_tree/asv_table.relative.xls) |
| asv_table.txt | ASV 特征表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_genus_tree/asv_table.txt) |
| feature.fasta | ASV 代表序列 | FASTA | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_genus_tree/feature.fasta) |
| asv_table_group.g.relative.xls | 分组属水平相对丰度表（可选） | XLS | 16S/18S/ITS | 通用 | - |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| selOTUs/ | Top 属 OTU 筛选结果 | 目录 | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree/genus_100.tree.png | 样本属进化树 | PNG | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree/genus_100.tree.pdf | 样本属进化树 | PDF | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree/genus_100.tree.svg | 样本属进化树 | SVG | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree_group/genus_group_100.tree.png | 分组属进化树（可选） | PNG | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree_group/genus_group_100.tree.pdf | 分组属进化树（可选） | PDF | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree_group/genus_group_100.tree.svg | 分组属进化树（可选） | SVG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_genus_tree.sh \
    -t all_tax_assignments.txt \
    -g asv_table.g.relative.xls \
    -r asv_table.relative.xls \
    -a asv_table.txt \
    -s feature.fasta \
    -o GenusTree_Output/
# 输出目录：GenusTree_Output/；文件：genus_evolutionary_tree/genus_100.tree.*
```

**示例 1**：样本属进化树
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_genus_tree.sh \
    -t all_tax_assignments.txt \
    -g Relative/asv_table.g.relative.xls \
    -r Relative/asv_table.s.relative.xls \
    -a asv_table.txt \
    -s feature.fasta \
    -o GenusTree_Output/
```

**示例 2**：样本 + 分组属进化树
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_genus_tree.sh \
    -t all_tax_assignments.txt \
    -g Relative/asv_table.g.relative.xls \
    -r Relative/asv_table.s.relative.xls \
    -a asv_table.txt \
    -s feature.fasta \
    -G Relative_group/asv_table_group.g.relative.xls \
    -o GenusTree_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -t, --taxonomy | 物种注释表路径 | 是 | - | all_tax_assignments.txt |
| -g, --genus-table | 属水平相对丰度表（样本） | 是 | - | asv_table.g.relative.xls |
| -r, --relative-table | 样本相对丰度表（select_OTUs --otutab） | 是 | - | asv_table.relative.xls |
| -a, --asv-table | ASV 特征表路径 | 是 | - | asv_table.txt |
| -s, --asv-seqs | ASV 代表序列路径 | 是 | - | feature.fasta |
| -G, --group-genus-table | 分组属水平相对丰度表 | 否 | - | asv_table_group.g.relative.xls |
| -o, --output | 输出目录 | 是 | - | GenusTree_Output/ |

---

## 流程步骤

```
1️⃣ select_OTUs.pl（筛选属水平 Top 物种）
   ↓
2️⃣ make_genus_table.pl（构建属序列与门分类列表）
   ↓
3️⃣ del.pl（过滤序列）
   ↓
4️⃣ 多序列比对（muscle / align_seqs.py）
   ↓
5️⃣ 构建进化树（make_phylogeny.py）
   ↓
6️⃣ 准备丰度矩阵 + circle_tree.pl 绘制环形树
   ↓
7️⃣ SVG → PNG/PDF（convert）
   ↓
8️⃣ 分组属进化树（提供 -G 时重复 2–7）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **select_OTUs.pl**: `.../00.Commbin/test_bin/select_OTUs.pl`
- **make_genus_table.pl / del.pl / circle_tree.pl**: `.../03.ASV/lib/`
- **QIIME1**: `QIIME1_CONDA_BIN` + `QIIME1_ENV`（默认 qiime1）
- **convert**: `/usr/bin/convert` (ImageMagick)

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SELECT_TOP_N | select_OTUs 筛选 Top N | 10 |
| TREE_TOP_N | 进化树 Top N 属 | 100 |
| CONVERT_BIN | ImageMagick convert 路径 | /usr/bin/convert |

### 自定义路径（迁移环境时）

```bash
export PERL_BIN="/usr/bin/perl"
export QIIME1_CONDA_BIN="/your/path/to/miniconda3/bin"
export QIIME1_ENV="qiime1"
export CONVERT_BIN="/usr/bin/convert"
bash step3_genus_tree.sh ... -o GenusTree_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_taxonomy | all_tax_assignments.txt | 物种注释表 |
| step3_table_stats | asv_table.g.relative.xls, asv_table.relative.xls | 相对丰度表 |
| step3_feature_tables | asv_table.txt | ASV 特征表 |
| step3_dada2 | feature.fasta | ASV 代表序列 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | genus_100.tree.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step3_genus_tree.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step3_genus_tree.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step3_genus_tree/`
- **参考流程**: `Step9.GenusTree.sh`

---

最后更新：2026-06-24
