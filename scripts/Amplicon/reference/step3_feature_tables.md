# Feature Tables - ASV 特征表构建模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | feature_tables |
| **Description** | 构建包含物种注释信息的 ASV 特征表，生成标准化格式用于下游分析 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组组成分析 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| featureTable.biom | ASV 丰度表（BIOM 格式） | BIOM | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_feature_tables/asv_table.txt) |
| all_tax_assignments.txt | 物种注释结果 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_feature_tables/all_tax_assignments.txt) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.txt | 标准化 ASV 特征表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_table_stats/asv_table.txt) |
| featureTaxonomy.biom | 带物种注释的 BIOM 表 | BIOM | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_feature_tables.sh -i featureTable.biom -t all_tax_assignments.txt
# 输出：asv_table.txt, featureTaxonomy.biom
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_feature_tables.sh -i featureTable.biom -t all_tax_assignments.txt
# 输出：asv_table.txt, featureTaxonomy.biom
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | BIOM 格式特征表路径 | 是 | - | featureTable.biom |
| -t, --taxonomy | 物种注释文件路径 | 是 | - | all_tax_assignments.txt |

---

## 流程步骤

```
1️⃣ biom add-metadata（添加物种注释到 BIOM 表）
   ↓
2️⃣ biom convert（BIOM → TSV 转换）
   ↓
3️⃣ 格式标准化（sed 处理表头和分隔符）
```

---

## asv_table.txt 格式

```
#OTU_num	D1	D2	D3	...	Taxonomy
ASV0	10251	9932	8354	...	k__Bacteria;p__Bacteroidota;c__Bacteroidia;...
ASV1	7446	7723	4762	...	k__Bacteria;p__Bacteroidota;c__Bacteroidia;...
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **conda**: `/software/anaconda3/bin/conda`
- **biom**: `/software/anaconda3/envs/16s-env/bin/biom`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CONDA_BIN="/your/path/to/conda"' > .env
echo 'export BIOM_BIN="/your/path/to/biom"' >> .env
source .env
bash step3_feature_tables.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_dada2 | featureTable.biom | ASV 丰度表 |
| step3_taxonomy | all_tax_assignments.txt | 物种注释表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.txt | 表统计分析 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step3_feature_tables.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step3_feature_tables.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step3_feature_tables/`

---

最后更新：2026-04-15
