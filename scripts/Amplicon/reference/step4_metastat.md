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
| asv_table.even.txt | 均一化 ASV 表（step3 输出） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_metastat/asv_table.even.txt) |
| group.list | 样本分组列表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_metastat/group.list) |
| Vs.list | 对比组列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_metastat/Vs.list) |

**注**：`Evenabs/`、`Relative/`、`group_col.list` 均由脚本内部自动生成，无需手动准备。

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| group_col.list | 分组颜色配置（由 group.list 生成） | TSV | 16S/18S/ITS | 通用 | - |
| Evenabs/ | 各层级绝对丰度表（asv_table.{p,c,...}.absolute.xls） | DIR | 16S/18S/ITS | 通用 | - |
| Relative/ | 各层级相对丰度表（asv_table.{p,c,...}.relative.xls） | DIR | 16S/18S/ITS | 通用 | - |
| phylum/ ~ species/ | 各层级 MetaStat 差异分析结果 | DIR | 16S/18S/ITS | 通用 | - |
| */boxplot/ | 差异物种箱线图 | DIR | 16S/18S/ITS | 通用 | - |
| */Diff_heatmap/ | 差异物种热图（annotation.heatmap.pdf/png） | DIR | 16S/18S/ITS | 通用 | - |
| */metastat.fin | 完成标记文件 | FIN | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_metastat.sh \
    -e TableStats/asv_table.even.txt \
    -g group.list \
    -v Vs.list \
    -o MetaStat_Output/
```

**示例**（仅分析门和属水平）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_metastat.sh \
    -e TableStats/asv_table.even.txt \
    -g group.list \
    -v Vs.list \
    -l phylum,genus \
    -o MetaStat_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -e, --even | 均一化 ASV 表 asv_table.even.txt | 是 | - | TableStats/asv_table.even.txt |
| -g, --group | 分组列表路径 | 是 | - | group.list |
| -v, --vs-list | 对比组列表路径 | 是 | - | Vs.list |
| -l, --levels | 分析层级（逗号分隔，默认全部） | 否 | phylum,class,order,family,genus,species | phylum,genus 或 p,g |
| -o, --output | 输出目录 | 是 | - | MetaStat_Output/ |

**`-l` 可选值**：

| 全称 | 简写 |
|------|------|
| phylum | p |
| class | c |
| order | o |
| family | f |
| genus | g |
| species | s |

---

## Vs.list 格式

```
# 对比组列表（Tab 分隔两组名）
T100	T200
T109	T209
```

**说明**：
- 每行定义一组对比（Group1 vs Group2）
- 分组名称必须与 `group.list` 中的分组名称一致
- 支持多组对比

---

## 分析层级

| 层级 | 代码 | 输出目录 | Evenabs 输入 | Relative 输入 |
|------|------|---------|-------------|--------------|
| **门** | p | phylum/ | asv_table.p.absolute.xls | asv_table.p.relative.xls |
| **纲** | c | class/ | asv_table.c.absolute.xls | asv_table.c.relative.xls |
| **目** | o | order/ | asv_table.o.absolute.xls | asv_table.o.relative.xls |
| **科** | f | family/ | asv_table.f.absolute.xls | asv_table.f.relative.xls |
| **属** | g | genus/ | asv_table.g.absolute.xls | asv_table.g.relative.xls |
| **种** | s | species/ | asv_table.s.absolute.xls | asv_table.s.relative.xls |

---

## 流程步骤

```
0️⃣ color_defined.pl：group.list → group_col.list
   ↓
1️⃣ stat_otu_tab.pl：asv_table.even.txt → Evenabs/ 绝对丰度表
   ↓
2️⃣ stat_otu_tab.pl：asv_table.even.txt → Relative/ 相对丰度表
   ↓
3️⃣ MetaStat1.3.benjamini.R：Evenabs/ 一次分析全部层级（R 脚本无终端输出）
   ↓
4️⃣ 按 -l 选定层级循环：
   ├─ Metastat_boxplot.pl（箱线图，使用 group_col.list 配色）
   └─ complex.pl（差异物种热图）
   ↓
5️⃣ 生成完成标记 metastat.fin
```

**说明**：
- MetaStat R 脚本的 `--infilepath` 指向扁平的 `Evenabs/` 目录（非 `Evenabs/genus/` 子目录），结果自动写入 `genus/`、`phylum/` 等子目录
- 指定 `-l` 时，Evenabs/ 与 Relative/ 也仅生成对应层级文件

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`
- **stat_otu_tab.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl`
- **Rscript**: `/gfs/softwares/R/3.6.3/bin/Rscript`
- **MetaStat1.3.benjamini.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/metastat/MetaStat1.3.benjamini.R`
- **Metastat_boxplot.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/metastat/metabox/Metastat_boxplot.pl`
- **complex.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/brief_report_heatmap/complex.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

```bash
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' > .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
echo 'export STAT_OTU_TAB_PL="/your/path/to/stat_otu_tab.pl"' >> .env
echo 'export METASTAT_R="/your/path/to/MetaStat1.3.benjamini.R"' >> .env
echo 'export METASTAT_BOXPLOT_PL="/your/path/to/Metastat_boxplot.pl"' >> .env
echo 'export COMPLEX_PL="/your/path/to/complex.pl"' >> .env
source .env
bash step4_metastat.sh ... -o MetaStat_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt | 均一化 ASV 表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | */Diff_heatmap/ | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step4_metastat.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step4_metastat.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step4_metastat/`

---

最后更新：2026-06-26
