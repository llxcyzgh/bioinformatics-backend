# Convert Table - 表格转 QIIME2 格式模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | convert_table |
| **Description** | 将 TSV/BIOM 格式特征表转换为 QIIME2 QZA 格式，供下游 QIIME2 分析使用 |
| **适用范围** | 16S/18S/ITS 扩增子测序、QIIME2 格式转换 |
| **估算机时** | 0 小时 |
| **报价分数** | 0 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.txt | ASV 特征表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_convert_table/asv_table.txt) |
| asv_table.even.txt | 均一化 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_convert_table/asv_table.even.txt) |
| featureTable.biom | ASV 丰度表 | BIOM | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_convert_table/featureTable.biom) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| {basename}.biom | BIOM 中间文件（仅 TSV 输入时生成） | BIOM | 16S/18S/ITS | 通用 | - |
| {basename}.qza | QIIME2 特征表 | QZA | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_convert_table.sh -i <table> -o ConvertTable_Output/
# 输出目录：ConvertTable_Output/；文件：{basename}.qza
```

**示例 1**：TSV 转 QZA
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_convert_table.sh -i asv_table.even.txt -o ConvertTable_Output/
# 输出目录：ConvertTable_Output/；文件：asv_table.even.biom, asv_table.even.qza
```

**示例 2**：BIOM 直接转 QZA
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_convert_table.sh -i featureTable.biom -o ConvertTable_Output/
# 输出目录：ConvertTable_Output/；文件：featureTable.qza
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 输入表格文件路径（TSV/BIOM） | 是 | - | asv_table.even.txt |
| -o, --output | 输出目录 | 是 | - | ConvertTable_Output/ |
| -t, --type | QIIME2 数据类型 | 否 | FeatureTable[Frequency] | FeatureTable[Frequency] |
| --table-type | BIOM 表格类型（TSV 转 BIOM 时使用） | 否 | OTU table | OTU table |
| -h, --help | 显示帮助信息 | 否 | - | - |

### QIIME2 类型选项

| -t 值 | 说明 |
|-------|------|
| FeatureTable[Frequency] | 特征丰度表（默认，用于 ASV/OTU 表） |
| FeatureData[Sequence] | 序列数据 |

### BIOM 表格类型选项

| --table-type 值 | 说明 |
|-----------------|------|
| OTU table | OTU/ASV 丰度表（默认） |
| Observation metadata | 观测元数据表 |

---

## 流程步骤

```
1️⃣ 检测输入格式
   ├─ TSV/TXT → biom convert（TSV → BIOM）
   └─ BIOM → 跳过此步
   ↓
2️⃣ qiime tools import（BIOM → QZA）
   ↓
输出：{basename}.qza
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **conda**: `/software/anaconda3/bin/activate`
- **conda 环境**: `16s-env`（内含 `biom`、`qiime`）

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CONDA_BIN="/your/path/to/anaconda3/bin"' > .env
echo 'export CONDA_ENV="16s-env"' >> .env
source .env
bash step3_convert_table.sh ... -o ConvertTable_Output/
```

也可通过 `MODULE_ENV_FILE` 加载统一配置：
```bash
export MODULE_ENV_FILE="/path/to/module.env"
bash step3_convert_table.sh -i asv_table.even.txt -o ConvertTable_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_feature_tables | asv_table.txt | 标准化 ASV 特征表 |
| step3_table_stats | asv_table.even.txt | 均一化 ASV 表 |
| step3_dada2 | featureTable.biom | DADA2 输出的 BIOM 丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step3_alpha_data | *.qza | Alpha 多样性分析（也可直接接受 TSV） |
| step3_beta_data | *.qza | Beta 多样性分析 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step3_convert_table.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step3_convert_table.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step3_convert_table/`

---

最后更新：2026-06-24
