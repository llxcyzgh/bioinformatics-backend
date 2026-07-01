# Taxa Summary Group - 物种组成热图模块（分组水平）

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | taxasummary_group |
| **Description** | 基于分组相对丰度表绘制物种组成热图，展示各分类层级的分组物种分布 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组物种组成可视化 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative_group/ | 分组相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_taxasummary_group/Relative_group/) |
| Relative/ | 样本相对丰度表目录（脚本内自动生成 Relative_group/） | DIR | 16S/18S/ITS | 通用 | - |
| asv_table.even.txt | 均一化 ASV 表（脚本内自动生成 Relative/ 与 Relative_group/） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_taxasummary_group/asv_table.even.txt) |
| group.list | 样本分组文件（-i 为 Relative/ 或 asv_table.even.txt 时必需） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_taxasummary_group/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| cluster.{level}.png/pdf | 各层级分组物种组成热图 | PNG/PDF | 16S/18S/ITS | 通用 | cluster.p.png, cluster.g.png |
| cluster.{level}.txt | 热图数据表 | TXT | 16S/18S/ITS | 通用 | cluster.p.txt |
| Relative/ | 由 asv_table.even.txt 生成的样本相对丰度表（可选） | DIR | 16S/18S/ITS | 通用 | - |
| Relative_group/ | 由 group.list 汇总的分组相对丰度表（可选） | DIR | 16S/18S/ITS | 通用 | - |

`{level}` 为所选分类层级代码：`p`、`c`、`o`、`f`、`g`、`s`。

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh -i Relative_group/ -o TaxaSummaryGroup_Output/
# 默认分析全部层级：phylum, class, order, family, genus, species
```

**示例 1**（Relative_group/ 目录）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh -i Relative_group/ -o TaxaSummaryGroup_Output/
```

**示例 2**（均一化 ASV 表，自动生成 Relative/ 与 Relative_group/）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh \
    -i TableStats/asv_table.even.txt \
    -g group.list \
    -o TaxaSummaryGroup_Output/
```

**示例 3**（已有 Relative/，仅生成分组表并绘图）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh \
    -i Relative/ \
    -g group.list \
    -o TaxaSummaryGroup_Output/
```

**示例 4**（仅指定层级）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh \
    -i Relative_group/ \
    -l phylum,genus \
    -o TaxaSummaryGroup_Output/
# 等价于 -l p,g
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | Relative_group/、Relative/ 目录或 asv_table.even.txt | 是 | - | Relative_group/ |
| -g, --group | 样本分组文件（-i 为 Relative/ 或 asv_table.even.txt 时必需） | 条件必需 | - | group.list |
| -l, --levels | 分析层级，逗号分隔 | 否 | 全部层级 | phylum,genus 或 p,g |
| --top | Top 物种数量 | 否 | 35 | 35 |
| -o, --output | 输出目录 | 是 | - | TaxaSummaryGroup_Output/ |

**可选层级**：`phylum(p)`、`class(c)`、`order(o)`、`family(f)`、`genus(g)`、`species(s)`

---

## 流程步骤

```
0️⃣（可选）stat_otu_tab.pl 生成 Relative/（-i 为 asv_table.even.txt 时）
   ↓
0️⃣（可选）Combine_table.pl + group.list 生成 Relative_group/（-i 为 asv_table.even.txt 或 Relative/ 时）
   ↓
1️⃣ heatmapData.py（生成热图数据）
   ↓
2️⃣ heatmapPlot.R（绘制热图）
   ↓
3️⃣ convert（PDF → PNG 转换）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **stat_otu_tab.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl`
- **Combine_table.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/Combine_table.pl`
- **python**: `/usr/bin/python`
- **heatmapData.py**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/heatmapData.py`
- **Rscript**: `/gfs/softwares/R/3.6.3/bin/Rscript`
- **heatmapPlot.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/heatmapPlot.R`
- **convert**: `/usr/bin/convert` (ImageMagick)

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export STAT_OTU_TAB_PL="/your/path/to/stat_otu_tab.pl"' >> .env
echo 'export COMBINE_TABLE_PL="/your/path/to/Combine_table.pl"' >> .env
echo 'export PYTHON_BIN="/your/path/to/python"' >> .env
echo 'export HEATMAP_DATA_PY="/your/path/to/heatmapData.py"' >> .env
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' >> .env
echo 'export HEATMAP_PLOT_R="/your/path/to/heatmapPlot.R"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
source .env
bash step4_taxasummary_group.sh ... -o TaxaSummaryGroup_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative_group/、asv_table.even.txt、Relative/ | 分组/样本相对丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | cluster.*.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step4_taxasummary_group.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step4_taxasummary_group/`

---

最后更新：2026-06-24
