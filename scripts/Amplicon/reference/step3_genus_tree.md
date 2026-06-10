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
| all_tax_assignments.txt | 物种注释表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_genus_tree/all_tax_assignments.txt) |
| asv_table.g.relative.xls | 属水平相对丰度表 | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_genus_tree/asv_table.g.relative.xls) |
| feature.fasta | ASV 代表序列 | FASTA | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_genus_tree/feature.fasta) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| genus_evolutionary_tree/genus_100.tree.png | 样本属进化树 | PNG | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree/genus_100.tree.pdf | 样本属进化树 | PDF | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree/genus_100.tree.svg | 样本属进化树 | SVG | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree_group/genus_group_100.tree.png | 分组属进化树 | PNG | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree_group/genus_group_100.tree.pdf | 分组属进化树 | PDF | 16S/18S/ITS | 通用 | - |
| genus_evolutionary_tree_group/genus_group_100.tree.svg | 分组属进化树 | SVG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_genus_tree.sh -t all_tax_assignments.txt -g asv_table.g.relative.xls -s feature.fasta
# 输出：genus_evolutionary_tree/genus_100.tree.*, genus_evolutionary_tree_group/genus_group_100.tree.*
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_genus_tree.sh -t all_tax_assignments.txt -g asv_table.g.relative.xls -s feature.fasta
# 输出：genus_evolutionary_tree/genus_100.tree.png, genus_evolutionary_tree_group/genus_group_100.tree.png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -t, --taxonomy | 物种注释表路径 | 是 | - | all_tax_assignments.txt |
| -g, --genus-table | 属水平相对丰度表路径 | 是 | - | asv_table.g.relative.xls |
| -s, --asv-seqs | ASV 代表序列路径 | 是 | - | feature.fasta |

---

## 流程步骤

```
1️⃣ select_OTUs.pl（筛选属水平 Top100 物种）
   ↓
2️⃣ make_genus_table.pl（构建属水平进化树输入）
   ↓
3️⃣ del.pl（过滤序列）
   ↓
4️⃣ 多序列比对（muscle）
   ↓
5️⃣ 构建进化树（make_phylogeny.py）
   ↓
6️⃣ 绘制环形树（circle_tree.pl）
   ↓
7️⃣ SVG → PNG/PDF 转换（convert）
   ↓
8️⃣ 分组属进化树（重复上述流程）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **conda**: `/gfs/users/guorongjun/miniconda3/bin/conda`
- **qiime1**: QIIME1 环境
- **perl 脚本路径**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/`
- **align_seqs.py**: QIIME1 脚本（muscle 比对）
- **make_phylogeny.py**: QIIME1 脚本（构建进化树）
- **convert**: `/usr/bin/convert` (ImageMagick)

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CONDA_BIN="/your/path/to/conda"' > .env
echo 'export QIIME1_ENV="/your/path/to/qiime1"' >> .env
echo 'export PERL_SCRIPTS_PATH="/your/path/to/perl/scripts"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
source .env
bash step3_genus_tree.sh ...
```
---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_taxonomy | all_tax_assignments.txt | 物种注释表 |
| step3_table_stats | asv_table.g.relative.xls | 属水平相对丰度表 |
| step3_dada2 | feature.fasta | ASV 代表序列 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | genus_100.tree.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step3_genus_tree.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step3_genus_tree.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step3_genus_tree/`

---

最后更新：2026-04-15
