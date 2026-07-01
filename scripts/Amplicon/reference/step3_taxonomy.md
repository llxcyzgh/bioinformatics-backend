# Taxonomy - 物种注释模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | taxonomy |
| **Description** | 基于 VSEARCH 的物种注释，将 ASV 代表序列与参考数据库比对得到分类学信息 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组物种注释 |
| **估算机时** | 2.0 小时 |
| **报价分数** | 3.6 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|------|
| featureSeqs.qza / feature.fasta | ASV 代表序列（QIIME2 或 FASTA） | QZA/FASTA | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_taxonomy/feature.fasta) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| taxonomy.tsv | 物种注释表（文本） | TSV | 16S/18S/ITS | 通用 | - |
| seq_taxonomy.qza | 物种注释结果（QIIME2） | QZA | 16S/18S/ITS | 通用 | - |
| all_tax_assignments.txt | 物种注释表（链接） | TXT | 16S/18S/ITS | 通用 | - |

---


## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_taxonomy.sh -i <输入文件> -t <16S|18S|ITS> -p <threads> -o Taxonomy_Output/
# 输出目录：Taxonomy_Output/；文件：seq_taxonomy.qza, taxonomy.tsv, all_tax_assignments.txt
```

**示例 1**：使用 step3_dada2 输出（qza 格式）
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_taxonomy.sh -i featureSeqs.qza -t 16S -p 16 -o Taxonomy_Output/
# 输出目录：Taxonomy_Output/；文件：seq_taxonomy.qza, taxonomy.tsv, all_tax_assignments.txt
```

**示例 2**：使用用户提供的 FASTA 文件
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_taxonomy.sh -i ASV_representative_sequences.fasta -t 16S -p 16 -o Taxonomy_Output/
# 自动转换：ASV_representative_sequences.fasta → featureSeqs_temp.qza
# 输出目录：Taxonomy_Output/；文件：seq_taxonomy.qza, taxonomy.tsv, all_tax_assignments.txt
```
### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 输入文件路径（.qza 或 .fasta/.fa/.fna） | 是 | - | featureSeqs.qza 或 sequences.fasta |
| -t, --type | 扩增子类型 | 是 | 16S | 16S、18S 或 ITS |
| -p, --threads | 线程数 | 否 | 16 | 16 |
| -o, --output | 输出目录 | 是 | - | Taxonomy_Output/ |

---

## 参考数据库

### 16S 数据库

| 文件 | 路径 |
|------|------|
| 序列 | `/database/amplicon/Qiime2_SILVA_v138.1/16S.Bac.Arc/silva_138.1_99_16S.qza` |
| 注释 | `/database/amplicon/Qiime2_SILVA_v138.1/16S.Bac.Arc/silva_138.1_99_16S_taxonomy.qza` |

### 18S 数据库

| 文件 | 路径 |
|------|------|
| 序列 | `/database/amplicon/Qiime2_SILVA_v138.1/18S.Eukaryota/silva_Eukaryota.qza` |
| 注释 | `/database/amplicon/Qiime2_SILVA_v138.1/18S.Eukaryota/silva_Eukaryota.taxonmy.qza` |

### ITS 数据库

| 文件 | 路径 |
|------|------|
| 序列 | `/database/amplicon/Qiime2_unite99_v9.0/unitev9.0_seq_99.qza` |
| 注释 | `/database/amplicon/Qiime2_unite99_v9.0/unitev9.0_tax_99.qza` |

---

## 流程步骤

```
1️⃣ 检测输入格式（.qza 或 .fasta）
   ↓
2️⃣ FASTA? → 转换为 qza（自动）
   ↓
3️⃣ VSEARCH 比对（classify-consensus-vsearch）
   ↓
4️⃣ 导出注释结果（seq_taxonomy.qza）
   ↓
5️⃣ 格式化处理（sed 替换）
   ↓
6️⃣ 生成最终注释表（taxonomy.tsv）
   ↓
7️⃣ 清理临时文件（如果是转换的）
```

---
## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **conda**: `/software/anaconda3/bin/conda`
- **qiime**: `/software/anaconda3/envs/16s-env/bin/qiime`

**参考数据库路径**：
- **16S 序列**: `/database/amplicon/Qiime2_SILVA_v138.1/16S.Bac.Arc/silva_138.1_99_16S.qza`
- **16S 注释**: `/database/amplicon/Qiime2_SILVA_v138.1/16S.Bac.Arc/silva_138.1_99_16S_taxonomy.qza`
- **18S 序列**: `/database/amplicon/Qiime2_SILVA_v138.1/18S.Eukaryota/silva_Eukaryota.qza`
- **18S 注释**: `/database/amplicon/Qiime2_SILVA_v138.1/18S.Eukaryota/silva_Eukaryota.taxonmy.qza`
- **ITS 序列**: `/database/amplicon/Qiime2_unite99_v9.0/unitev9.0_seq_99.qza`
- **ITS 注释**: `/database/amplicon/Qiime2_unite99_v9.0/unitev9.0_tax_99.qza`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CONDA_BIN="/your/path/to/conda"' > .env
echo 'export QIIME_BIN="/your/path/to/qiime"' >> .env
echo 'export SILVA_16S_SEQ="/your/path/to/silva_138.1_99_16S.qza"' >> .env
echo 'export SILVA_16S_TAX="/your/path/to/silva_138.1_99_16S_taxonomy.qza"' >> .env
echo 'export SILVA_18S_SEQ="/your/path/to/silva_Eukaryota.qza"' >> .env
echo 'export SILVA_18S_TAX="/your/path/to/silva_Eukaryota.taxonmy.qza"' >> .env
echo 'export UNITE_SEQ="/your/path/to/unitev9.0_seq_99.qza"' >> .env
echo 'export UNITE_TAX="/your/path/to/unitev9.0_tax_99.qza"' >> .env
source .env
bash step3_taxonomy.sh ... -o Taxonomy_Output/
```
---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_dada2 | featureSeqs.qza | ASV 代表序列 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step4_diversity | taxonomy.tsv | 多样性分析 |
| step4_taxa | taxonomy.tsv | 物种组成分析 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step3_taxonomy.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step3_taxonomy.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step3_taxonomy/`

---

最后更新：2026-06-24
