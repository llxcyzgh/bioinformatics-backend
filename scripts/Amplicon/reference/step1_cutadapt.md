# Cutadapt - 引物修剪模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | cutadapt |
| **Description** | 从双端测序 FASTQ 数据中去除引物序列，支持多样本并行处理 |
| **适用范围** | 16S/18S/ITS 扩增子测序、未去除引物的双端测序数据 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| ${sample}.R1.fastq.gz | 前向测序文件 (双端) | FASTQ.GZ | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step1_cutadapt/CKM031.R1.fastq.gz) |
| ${sample}.R2.fastq.gz | 反向测序文件 (双端) | FASTQ.GZ | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step1_cutadapt/CKM031.R2.fastq.gz) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| ${sample}.cutadapt.R1.fastq.gz | 去除引物后的前向 fastq 数据 | FASTQ.GZ | 16S/18S/ITS | 通用 | - |
| ${sample}.cutadapt.R2.fastq.gz | 去除引物后的反向 fastq 数据 | FASTQ.GZ | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step1_cutadapt.sh -r1 <样本名>.R1.fastq.gz -r2 <样本名>.R2.fastq.gz -f <正向引物> -r <反向引物>
# 输出：<样本名>.cutadapt.R1.fastq.gz, <样本名>.cutadapt.R2.fastq.gz
```

**示例**（16S V3-V4）：
```bash
# 样本 Sample001
bash step1_cutadapt.sh -r1 Sample001.R1.fastq.gz -r2 Sample001.R2.fastq.gz -f ACTCCTACGGGAGGCAGCAG -r GGACTACHVGGGTWTCTAAT
# 输出：Sample001.cutadapt.R1.fastq.gz, Sample001.cutadapt.R2.fastq.gz
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -r1, --r1-path | 前向测序文件路径 | 是 | - | CKM031.R1.fastq.gz |
| -r2, --r2-path | 反向测序文件路径 | 是 | - | CKM031.R2.fastq.gz |
| -f, --f-primer | 前向引物序列 | 是 | - | ACTCCTACGGGAGGCAGCAG |
| -r, --r-primer | 反向引物序列 | 是 | - | GGACTACHVGGGTWTCTAAT |
| -e, --error-rate | 错误率 | 否 | 0.1 | 0.1 |
| -l, --min-length | 最小长度阈值 | 否 | 100 | 100 |
| -n, --threads | 线程数 | 否 | 1 | 12 |

---

## 常见引物序列

| 引物类型 | 前向引物 | 反向引物 | 扩增子长度 |
|------|------|------|----------|
| **16S V3-V4** | ACTCCTACGGGAGGCAGCAG | GGACTACHVGGGTWTCTAAT | ~460bp |
| **16S V4** | GTGCCAGCMGCCGCGGTAA | GGACTACHVGGGTWTCTAAT | ~250bp |
| **ITS1** | CTTGGTCATTTAGAGGAAGTAA | GCTGCGTTCTTCATCGATGC | ~300bp |
| **ITS2** | GCATCGATGAAGAACGCAGC | TCCTCCGCTTATTGATATGC | ~350bp |

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **cutadapt**: `/software/anaconda3/envs/16s-env/bin/cutadapt`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CUTADAPT_BIN="/your/path/to/cutadapt"' > .env
source .env
bash step1_cutadapt.sh ...
```
---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step1_cutadapt.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step1_cutadapt.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step1_cutadapt/`

---

最后更新：2026-04-15
