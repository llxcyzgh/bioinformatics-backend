# MetaStat - 组间差异物种分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | metastat |
| **Description** | MetaStat 分析，基于 F 检验和 Benjamini-Hochberg 校正识别组间显著差异物种 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组差异物种筛选 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| evenabs/ | 均一化绝对丰度表目录（各层级） | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_metastat/evenabs/) |
| group.list | 样本分组列表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_metastat/group.list) |
| Vs.list | 对比组列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_metastat/Vs.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| phylum/ | 门水平分析结果 | DIR | 16S/18S/ITS | 通用 | - |
| class/ | 纲水平分析结果 | DIR | 16S/18S/ITS | 通用 | - |
| order/ | 目水平分析结果 | DIR | 16S/18S/ITS | 通用 | - |
| family/ | 科水平分析结果 | DIR | 16S/18S/ITS | 通用 | - |
| genus/ | 属水平分析结果 | DIR | 16S/18S/ITS | 通用 | - |
| species/ | 种水平分析结果 | DIR | 16S/18S/ITS | 通用 | - |
| */Diff_heatmap/ | 差异物种热图 | DIR | 16S/18S/ITS | 通用 | - |
| */metastat.fin | 完成标记文件 | FIN | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_metastat.sh -e evenabs/ -g group.list -v Vs.list
# 输出：phylum/, class/, order/, family/, genus/, species/
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_metastat.sh -e evenabs/ -g group.list -v Vs.list
# 输出：phylum/, class/, order/, family/, genus/, species/, */Diff_heatmap/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -e, --evenabs | 均一化绝对丰度表目录 | 是 | - | evenabs/ |
| -g, --group | 分组列表路径 | 是 | - | group.list |
| -v, --vs-list | 对比组列表路径 | 是 | - | Vs.list |

---

## Vs.list 格式

```
# 对比组列表
# 格式：Group1_vs_Group2
D_vs_DF
Y_vs_Z
```

**说明**：
- 每行定义一组对比（Group1_vs_Group2）
- 分组名称必须与 `group.list` 中的分组名称一致
- 支持多组对比

---

## 分析层级

| 层级 | 代码 | 输出目录 | 输入文件 |
|------|------|---------|---------|
| **门** | p | phylum/ | asv_table.p.relative.xls |
| **纲** | c | class/ | asv_table.c.relative.xls |
| **目** | o | order/ | asv_table.o.relative.xls |
| **科** | f | family/ | asv_table.f.relative.xls |
| **属** | g | genus/ | asv_table.g.relative.xls |
| **种** | s | species/ | asv_table.s.relative.xls |

---

## 流程步骤

```
1️⃣ MetaStat1.3.benjamini.R（F 检验 + BH 校正）
   ↓
2️⃣ Metastat_boxplot.pl（箱线图绘制）
   ↓
3️⃣ complex.pl（差异物种热图）
   ↓
4️⃣ 生成完成标记（metastat.fin）
   ↓
5️⃣ 重复上述流程（6 个分类层级）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **Rscript**: `/gfs/softwares/R/3.6.3/bin/Rscript`
- **MetaStat1.3.benjamini.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/metastat/MetaStat1.3.benjamini.R`
- **Metastat_boxplot.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/metastat/metabox/Metastat_boxplot.pl`
- **complex.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/brief_report_heatmap/complex.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' > .env
echo 'export METASTAT_R="/your/path/to/MetaStat1.3.benjamini.R"' >> .env
echo 'export METASTAT_BOXPLOT_PL="/your/path/to/Metastat_boxplot.pl"' >> .env
echo 'export COMPLEX_PL="/your/path/to/complex.pl"' >> .env
source .env
bash step4_metastat.sh ...
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
| 报告生成 | */Diff_heatmap/ | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_metastat.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_metastat.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_metastat/`

---

最后更新：2026-04-15
