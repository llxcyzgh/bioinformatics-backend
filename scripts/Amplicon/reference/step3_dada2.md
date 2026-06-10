# DADA2 - ASV 推断与降噪模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | dada2 |
| **Description** | 基于错误模型的扩增子序列变异（ASV）推断工具，通过去噪算法生成高分辨率的生物序列变异体 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组多样性分析 |
| **估算机时** | 8.0 小时 |
| **报价分数** | 14.4 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| manifest.tsv | 样本与序列文件路径的对应关系表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_dada2/manifest.tsv) |
| ${sample}.fastq | 质控后的序列文件（由 manifest 引用） | FASTQ | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_dada2/D1.fastq.gz) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| featureSeqs.qza | ASV 代表序列（QIIME2） | QZA | 16S/18S/ITS | 通用 | - |
| feature-table.tsv | ASV 丰度表（已排序） | TSV | 16S/18S/ITS | 通用 | - |
| feature.fasta | ASV 代表序列 | FASTA | 16S/18S/ITS | 通用 | - |
| featureTable.qza | ASV 丰度表（QIIME2） | QZA | 16S/18S/ITS | 通用 | - |
| featureTable.biom | ASV 丰度表（BIOM） | BIOM | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_dada2.sh -m manifest.tsv -t <trunc_len> -n <threads>
# 输出：featureSeqs.qza, feature-table.tsv, feature.fasta, featureTable.qza, featureTable.biom
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_dada2.sh -m manifest.tsv -t 0 -n 12
# 输出：featureSeqs.qza, feature-table.tsv, feature.fasta, featureTable.qza, featureTable.biom
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -m, --manifest | manifest 文件路径 | 是 | - | manifest.tsv |
| -t, --trunc-len | 截断长度 | 否 | 0 | 0 |
| -n, --threads | 线程数 | 否 | 12 | 12 |
| -a, --min-asv | 最小 ASV 丰度 | 否 | 1 | 1 |

---

## manifest 文件格式

```
sample-id	absolute-filepath
D1	/path/to/project/02.Frags_QC/D1/D1.fastq
D2	/path/to/project/02.Frags_QC/D2/D2.fastq
D3	/path/to/project/02.Frags_QC/D3/D3.fastq
```

**说明**：
- `sample-id`: 样本名
- `absolute-filepath`: 质控后序列文件的绝对路径（`${sample}.fastq`）

---

## 流程步骤

```
1️⃣ 导入序列到 QIIME2 (allFastq.qza)
   ↓
2️⃣ DADA2 去噪 (dada2 denoise-single)
   ↓
3️⃣ 导出结果 (table, repseq, stats)
   ↓
4️⃣ 格式转换 (BIOM ↔ TSV)
   ↓
5️⃣ ASV 排序与过滤
   ↓
6️⃣ 导入回 QIIME2 (featureTable.qza, featureSeqs.qza)
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **conda**: `/software/anaconda3/bin/conda`
- **qiime**: `/software/anaconda3/envs/16s-env/bin/qiime`
- **biom**: `/software/anaconda3/envs/16s-env/bin/biom`
- **filter_name.py**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/filter_name.py`
- **asv_sort.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/asv_sort.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CONDA_BIN="/your/path/to/conda"' > .env
echo 'export QIIME_BIN="/your/path/to/qiime"' >> .env
echo 'export BIOM_BIN="/your/path/to/biom"' >> .env
source .env
bash step3_dada2.sh ...
```

---


## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step3_taxonomy | featureSeqs.qza | 物种注释 |
| step3_phylogeny | featureSeqs.qza | 系统发育树构建 |
| step4_diversity | featureTable.qza | 多样性分析 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step3_dada2.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step3_dada2.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step3_dada2/`

---

最后更新：2026-04-15
