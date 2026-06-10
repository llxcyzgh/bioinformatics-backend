# Import_Fasta - FASTA 导入 QIIME2 模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | import_fasta |
| **Description** | 将 FASTA 序列文件导入为 QIIME2 格式，用于后续 QIIME2 分析 |
| **适用范围** | 16S/18S/ITS 扩增子测序、任何 QIIME2 分析前置步骤 |
| **估算机时** | 0 小时 |
| **报价分数** | 0 |

---

## 输入

| 文件 | 描述 | 格式 | 适用组学 | 适用物种 |
|------|------|------|----------|----------|
| `sequences.fasta` | FASTA 序列文件 | FASTA | 16S/18S/ITS | 通用 |

---

## 输出

| 文件 | 描述 | 格式 | 适用组学 | 适用物种 |
|------|------|------|----------|----------|
| `featureSeqs.qza` | QIIME2 格式序列文件 | QZA | 16S/18S/ITS | 通用 |

---

## 执行命令

### 调用脚本（推荐）

```bash
bash ${AMPLICON_ROOT}/scripts/step0_import_fasta.sh \
    -i sequences.fasta \
    -o Import_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| `-i, --input` | 输入 FASTA 文件 | ✅ | - | sequences.fasta |
| `-o, --output` | 输出目录 | ✅ | - | Import_Output/ |
| `-t, --type` | QIIME2 类型 | ❌ | FeatureData[Sequence] | FeatureData[Sequence] |

---

## QIIME2 类型说明

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **FeatureData[Sequence]** | 特征数据序列 | ASV/OTU 代表序列 |
| **SampleData[SequencesWithQuality]** | 带质量的样本序列 | 原始测序数据 |
| **SampleData[JoinedSequencesWithQuality]** | 拼接后的序列 | FLASH 拼接后的数据 |

---

## 完整流程示例

### 场景 1: 只有 FASTA 文件，做物种注释

```bash
# Step 1: 导入为 QIIME2 格式
bash ${AMPLICON_ROOT}/scripts/step0_import_fasta.sh \
    -i sequences.fasta \
    -o Import_Output/

# Step 2: 物种注释
bash ${AMPLICON_ROOT}/scripts/step3_taxonomy.sh \
    -i Import_Output/featureSeqs.qza \
    -o Taxonomy_Output/ \
    -t 16S \
    -p 16
```

### 场景 2: 已有 QIIME2 格式，直接注释

```bash
# 直接进行物种注释
bash ${AMPLICON_ROOT}/scripts/step3_taxonomy.sh \
    -i featureSeqs.qza \
    -o Taxonomy_Output/ \
    -t 16S \
    -p 16
```

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step0_import_fasta.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step0_import_fasta.md`

---

## 相关模块

| 模块 | 脚本 | 用途 |
|------|------|------|
| **物种注释** | `step3_taxonomy.sh` | VSEARCH 物种注释 |
| **DADA2 分析** | `step3_dada2.sh` | ASV 推断与降噪 |
| **系统发育树** | `step3_phylogeny.sh` | 构建进化树 |

---

*最后更新：2026-04-13 | 扩增子智能体模块 v2.0*
