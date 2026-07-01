# Frags_QC - 序列质量控制模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | frags_qc |
| **Description** | 扩增子序列质量控制流程，包含质量过滤、去嵌合体、序列长度分布分析等步骤 |
| **适用范围** | 16S/18S/ITS 扩增子测序、宏基因组测序 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| ${sample}.extendedFrags.fastq | FLASH 拼接后的序列文件 | FASTQ | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step2_frags_qc/T1001.extendedFrags.fastq) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| ${sample}.fastq | 质控后序列 | FASTQ | 16S/18S/ITS | 通用 | - |
| ${sample}.fna | 质控后核酸序列 | FNA | 16S/18S/ITS | 通用 | - |
| ${sample}.json | fastp 质控统计信息 | JSON | 通用 | 通用 | - |
| ${sample}.html | fastp 质控报告（可视化） | HTML | 通用 | 通用 | - |
| ${sample}.fna.histograms.png | 序列长度分布图 | PNG | 16S/18S/ITS | 通用 | - |
| ng_QC/ | 详细质控统计目录 | DIR | 通用 | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step2_frags_qc.sh -i ${sample}.extendedFrags.fastq -q <quality> -u <max_n> -d <ref_db> -o Frags_QC_Output/
# 输出目录：Frags_QC_Output/；文件：${sample}.fastq, ${sample}.fna, ${sample}.json, ${sample}.html, ${sample}.fna.histograms.png, ng_QC/
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step2_frags_qc.sh -i D1.extendedFrags.fastq -q 19 -u 15 -o Frags_QC_Output/
# 输出目录：Frags_QC_Output/；文件：D1.fastq, D1.fna, D1.json, D1.html, D1.fna.histograms.png, ng_QC/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 输入 FASTQ 文件 | 是 | - | D1.extendedFrags.fastq |
| -q, --quality | 质量阈值 | 否 | 19 | 19 |
| -u, --max-n | 最大 N 比例 | 否 | 15 | 15 |
| -d, --ref-db | 参考数据库（去嵌合体） | 否 | - | silva_Bac.Arc.fasta |
| -o, --output | 输出目录 | 是 | - | Frags_QC_Output/ |

---

## 流程步骤

```
1️⃣ fastp 质量过滤
   ↓
2️⃣ 格式转换 (FASTQ → FASTA)
   ↓
3️⃣ VSEARCH 去嵌合体
   ↓
4️⃣ 提取非嵌合体序列
   ↓
5️⃣ 生成序列长度分布图
   ↓
6️⃣ 生成详细质控报告 (ng_QC)
```

---

## 质量控制标准

| 指标 | 优秀 | 合格 | 不合格 |
|------|------|------|--------|
| **Q20 比例** | >98% | 95-98% | <95% |
| **Q30 比例** | >90% | 85-90% | <85% |
| **去嵌合体保留率** | >85% | 70-85% | <70% |

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **fastp**: `/software/anaconda3/envs/prokka/bin/fastp`
- **vsearch**: `/software/anaconda3/pkgs/vsearch-2.7.0-1/bin/vsearch`
- **ng_QC**: `/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/qc/ng_QC`
- **Select_FqInFa.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/02.FragsQC/lib/Select_FqInFa.pl`
- **line_diagram.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/02.FragsQC/lib/line_diagram.pl`
- **convert**: `/usr/bin/convert`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export FASTP_BIN="/your/path/to/fastp"' > .env
echo 'export VSEARCH_BIN="/your/path/to/vsearch"' >> .env
echo 'export NG_QC_BIN="/your/path/to/ng_QC"' >> .env
source .env
bash step2_frags_qc.sh ... -o Frags_QC_Output/
```
---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step2_frags_qc.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step2_frags_qc.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step2_frags_qc/`

---

最后更新：2026-06-24
