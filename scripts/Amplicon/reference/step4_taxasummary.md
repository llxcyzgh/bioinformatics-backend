# Taxa Summary - 物种组成热图模块（样本水平）

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | taxasummary |
| **Description** | 基于相对丰度表绘制物种组成热图，展示各分类层级的物种分布 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组物种组成可视化 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative/ | 各分类层级相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_taxasummary/Relative/) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_taxasummary/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| cluster/cluster.p.png/pdf | 门水平物种组成热图 | PNG/PDF | 16S/18S/ITS | 通用 | - |
| cluster/cluster.c.png/pdf | 纲水平物种组成热图 | PNG/PDF | 16S/18S/ITS | 通用 | - |
| cluster/cluster.o.png/pdf | 目水平物种组成热图 | PNG/PDF | 16S/18S/ITS | 通用 | - |
| cluster/cluster.f.png/pdf | 科水平物种组成热图 | PNG/PDF | 16S/18S/ITS | 通用 | - |
| cluster/cluster.g.png/pdf | 属水平物种组成热图 | PNG/PDF | 16S/18S/ITS | 通用 | - |
| cluster/cluster.s.png/pdf | 种水平物种组成热图 | PNG/PDF | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_taxasummary.sh -i Relative/ -g group.list
# 输出：cluster/cluster.*.png/pdf
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_taxasummary.sh -i Relative/ -g group.list
# 输出：cluster/cluster.p.png, cluster/cluster.c.png, ..., cluster/cluster.s.png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 相对丰度表目录路径 | 是 | - | Relative/ |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| --top | Top 物种数量 | 否 | 35 | 35 |

---

## 流程步骤

```
1️⃣ heatmapData.py（生成热图数据，6 个层级）
   ↓
2️⃣ heatmapPlot.R（绘制热图，6 个层级）
   ↓
3️⃣ convert（PNG → PDF 转换）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
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
echo 'export PYTHON_BIN="/your/path/to/python"' > .env
echo 'export HEATMAP_DATA_PY="/your/path/to/heatmapData.py"' >> .env
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' >> .env
echo 'export HEATMAP_PLOT_R="/your/path/to/heatmapPlot.R"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
source .env
bash step4_taxasummary.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative/ | 各分类层级相对丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | cluster/cluster.*.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_taxasummary.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_taxasummary.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_taxasummary/`

---

最后更新：2026-04-15
