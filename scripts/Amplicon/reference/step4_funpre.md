# Funpre - PICRUSt2 功能预测分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | funpre (PICRUSt2) |
| **Description** | PICRUSt2 功能预测，基于 16S 序列预测功能基因和代谢通路，支持 TSV/BIOM 格式自动转换 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组功能预测 |
| **估算机时** | 2.0 小时 |
| **报价分数** | 3.6 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| featureTable.biom 或 featureTable.tsv | ASV 丰度表（BIOM 或 TSV 格式） | BIOM/TSV | 16S/18S/ITS | 细菌/古菌 | (${AMPLICON_ROOT}/examples/step4_funpre/featureTable.biom) |
| feature.fasta | ASV 代表序列 | FASTA | 16S/18S/ITS | 细菌/古菌 | (${AMPLICON_ROOT}/examples/step4_funpre/feature.fasta) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_funpre/group.list) |
| venng.list | 功能维恩图分组列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_funpre/venng.list) |

**注**：
- 支持 `.biom`、`.tsv`、`.txt` 格式的丰度表输入
- 如果是 TSV/TXT 格式，脚本会自动转换为 BIOM 格式
- `group.list` 和 `venng.list` 为可选输入，如不提供则跳过分组分析和功能维恩图

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| EC_metagenome_out/ | EC 酶功能预测结果 | DIR | 16S/18S/ITS | 细菌/古菌 | - |
| KO_metagenome_out/ | KO 通路预测结果 | DIR | 16S/18S/ITS | 细菌/古菌 | - |
| pathways_out/ | MetaCyc 通路预测结果 | DIR | 16S/18S/ITS | 细菌/古菌 | - |
| fun_venn_group/ | 功能维恩图（分组） | DIR | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_funpre.sh -b featureTable.biom -s feature.fasta [-g group.list] [-v venng.list]
# 输出：EC_metagenome_out/, KO_metagenome_out/, pathways_out/
```

**示例 1**：BIOM 格式输入
```bash
bash ${AMPLICON_ROOT}/scripts/step4_funpre.sh -b featureTable.biom -s feature.fasta -g group.list -v venng.list
# 输出：EC_metagenome_out/, KO_metagenome_out/, pathways_out/, fun_venn_group/
```

**示例 2**：TSV 格式输入（自动转换）
```bash
bash ${AMPLICON_ROOT}/scripts/step4_funpre.sh -b featureTable.tsv -s feature.fasta -g group.list -v venng.list
# 自动转换：featureTable.tsv → featureTable.biom
# 输出：EC_metagenome_out/, KO_metagenome_out/, pathways_out/, fun_venn_group/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -b, --biom | ASV 丰度表（BIOM 或 TSV 格式） | 是 | - | featureTable.biom 或 featureTable.tsv |
| -s, --seqs | ASV 代表序列（FASTA） | 是 | - | feature.fasta |
| -g, --group | 样本分组文件路径 | 否 | - | group.list |
| -v, --venn | 功能维恩图分组列表路径 | 否 | - | venng.list |

---

## TSV 格式要求

如果输入是 TSV 格式，需要符合以下格式：

```
#OTU_num	Sample1	Sample2	Sample3	...	Taxonomy
ASV0	10251	9932	8354	...	k__Bacteria;p__Bacteroidota;...
ASV1	7446	7723	4762	...	k__Bacteria;p__Bacteroidota;...
```

**说明**：
- 第一列为 ASV/OTU ID
- 后续列为样本丰度值
- 最后一列可为分类学信息（可选）
- 制表符（Tab）分隔

---

## venng.list 格式

```
# 空格分隔的分组名称（用于功能维恩图）
D DF Y Z
```

**说明**：
- 每行定义一组功能维恩图比较的分组
- 分组名称必须与 `group.list` 中的分组名称一致
- 支持 2-5 个分组的维恩图

---

## 流程步骤

```
0️⃣ 检测输入格式（TSV → BIOM 自动转换）
   ↓
1️⃣ PICRUSt2.pl（功能预测分析）
   ↓
2️⃣ EC 酶功能预测（EC_metagenome_out/）
   ↓
3️⃣ KO 通路预测（KO_metagenome_out/）
   ↓
4️⃣ MetaCyc 通路预测（pathways_out/）
   ↓
5️⃣ 功能维恩图（fun_venn_group/，可选）
   ↓
6️⃣ 清理临时 BIOM 文件（如果是 TSV 转换的）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **biom**: `/software/anaconda3/envs/16s-env/bin/biom`
- **PICRUSt2.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Funnction_prediction/PICRUSt2/PICRUSt2.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export BIOM_BIN="/your/path/to/biom"' >> .env
echo 'export PICRUSt2_PL="/your/path/to/PICRUSt2.pl"' >> .env
source .env
bash step4_funpre.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_dada2 | featureTable.biom | ASV 丰度表（BIOM） |
| step3_dada2 | feature.fasta | ASV 代表序列 |
| step3_feature_tables | asv_table.txt | ASV 丰度表（TSV） |
| step3_table_stats | group.list | 样本分组信息 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | EC_metagenome_out/ | 插入分析报告 |
| 报告生成 | KO_metagenome_out/ | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_funpre.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_funpre.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_funpre/`

---

最后更新：2026-04-15
