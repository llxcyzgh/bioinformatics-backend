# OTU Tree - 物种进化树可视化模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | otutree |
| **Description** | 基于 UPGMA 树和 Top10 物种丰度绘制带丰度信息的进化树 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组物种进化关系可视化 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

脚本**同一套参数**支持**样本**与**分组**两种分析，区别仅在于传入的上游文件路径不同。

### 样本水平

| 文件名 | 描述 | 格式 | 上游 | 示例路径 |
|--------|------|------|------|----------|
| *_weighted_unifrac_upgma.tre | Weighted UPGMA 树 | TRE | step3_upgma | UPGMA_Output/UPGMA_sample/unrarefied_bdiv/asv_table.even_weighted_unifrac_upgma.tre |
| *_unweighted_unifrac_upgma.tre | Unweighted UPGMA 树 | TRE | step3_upgma | UPGMA_Output/UPGMA_sample/unrarefied_bdiv/asv_table.even_unweighted_unifrac_upgma.tre |
| asv_table.p10.relative.xls | 门水平 Top10 物种丰度表（样本） | XLS | step3_top_species | TopSpecies_Output/top10/asv_table.p10.relative.xls |
| group.list | 样本分组文件（可选，用于树图分组着色） | TSV | 项目配置 | group.list |

### 分组水平（可选，需 step3_upgma `-G`、step3_top_species `-g`）

| 文件名 | 描述 | 格式 | 上游 | 示例路径 |
|--------|------|------|------|----------|
| *_weighted_unifrac_upgma.tre | 分组 Weighted UPGMA 树 | TRE | step3_upgma | UPGMA_Output/UPGMA_group/unrarefied_bdiv/asv_table.group.even_weighted_unifrac_upgma.tre |
| *_unweighted_unifrac_upgma.tre | 分组 Unweighted UPGMA 树 | TRE | step3_upgma | UPGMA_Output/UPGMA_group/unrarefied_bdiv/asv_table.group.even_unweighted_unifrac_upgma.tre |
| asv_table.p10.group.relative.xls | 门水平 Top10 物种丰度表（分组） | XLS | step3_top_species | TopSpecies_Output/top10_group/asv_table.p10.group.relative.xls |
| group.list | 样本分组文件（可选） | TSV | 项目配置 | group.list |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| UPGMA.W.tree.svg | Weighted UniFrac 树（SVG） | SVG | 16S/18S/ITS | 通用 | - |
| UPGMA.W.tree.png | Weighted UniFrac 树（PNG） | PNG | 16S/18S/ITS | 通用 | - |
| UPGMA.UnW.tree.svg | Unweighted UniFrac 树（SVG） | SVG | 16S/18S/ITS | 通用 | - |
| UPGMA.UnW.tree.png | Unweighted UniFrac 树（PNG） | PNG | 16S/18S/ITS | 通用 | - |

样本与分组各运行一次时，建议分别输出到 `OTUTree_sample/`、`OTUTree_group/`。

---

## 执行命令

**样本水平**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_otutree.sh \
    -w UPGMA_Output/UPGMA_sample/unrarefied_bdiv/asv_table.even_weighted_unifrac_upgma.tre \
    -u UPGMA_Output/UPGMA_sample/unrarefied_bdiv/asv_table.even_unweighted_unifrac_upgma.tre \
    -r TopSpecies_Output/top10/asv_table.p10.relative.xls \
    -g group.list \
    -o OTUTree_sample/
```

**分组水平**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_otutree.sh \
    -w UPGMA_Output/UPGMA_group/unrarefied_bdiv/asv_table.group.even_weighted_unifrac_upgma.tre \
    -u UPGMA_Output/UPGMA_group/unrarefied_bdiv/asv_table.group.even_unweighted_unifrac_upgma.tre \
    -r TopSpecies_Output/top10_group/asv_table.p10.group.relative.xls \
    -g group.list \
    -o OTUTree_group/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -w, --weighted-tree | Weighted UniFrac UPGMA 树 | 是 | - | asv_table.even_weighted_unifrac_upgma.tre |
| -u, --unweighted-tree | Unweighted UniFrac UPGMA 树 | 是 | - | asv_table.even_unweighted_unifrac_upgma.tre |
| -r, --relative | 门水平 Top10 丰度表（样本或分组） | 是 | - | asv_table.p10.relative.xls / asv_table.p10.group.relative.xls |
| -g, --group | 分组文件（传给 draw_tree.pl `--group` 着色） | 否 | - | group.list |
| -o, --output | 输出目录 | 是 | - | OTUTree_sample/ |

---

## 流程步骤

```
1️⃣ draw_tree.pl + --group（Weighted 树 + Top10 丰度柱）
   ↓
2️⃣ svg2xxx（SVG → PNG）
   ↓
3️⃣ draw_tree.pl + --group（Unweighted 树 + Top10 丰度柱）
   ↓
4️⃣ svg2xxx（SVG → PNG）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **draw_tree.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/draw_tree.pl`
- **svg2xxx**: `/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export DRAW_TREE_PL="/your/path/to/draw_tree.pl"' >> .env
echo 'export SVG2XXX_BIN="/your/path/to/svg2xxx"' >> .env
source .env
bash step4_otutree.sh ... -o OTUTree_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_upgma | UPGMA_sample/unrarefied_bdiv/*_upgma.tre | 样本 UPGMA 树 |
| step3_upgma | UPGMA_group/unrarefied_bdiv/*_upgma.tre | 分组 UPGMA 树（需 `-G`） |
| step3_top_species | top10/asv_table.p10.relative.xls | 样本门水平 Top10 |
| step3_top_species | top10_group/asv_table.p10.group.relative.xls | 分组门水平 Top10（需 `-g`） |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | UPGMA.W.tree.png, UPGMA.UnW.tree.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step4_otutree.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step4_otutree.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step4_otutree/`

---

最后更新：2026-06-24
