# Alpha Rarefaction - Alpha 多样性稀化曲线模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | alpha_rarefaction |
| **Description** | Alpha 多样性稀化曲线分析，包括 Rank Abundance 曲线和 Observed Features 稀化曲线 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Alpha 多样性分析 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_alpha_rarefaction/asv_table.even.txt) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_alpha_rarefaction/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| rank_abundance.svg/png | Rank Abundance 曲线 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| observed_features.svg/png | Observed Features 稀化曲线 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| alpha_diversity.svg/png | Alpha 多样性合并图 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| observed_features.group.svg/png | 分组稀化曲线 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| alpha_diversity.group.svg/png | 分组 Alpha 多样性合并图 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| group_otu_table.even.txt | 分组 ASV 表 | TSV | 16S/18S/ITS | 通用 | - |
| observed_features.group.xls | 分组稀化曲线数据 | XLS | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_alpha_rarefaction.sh -t asv_table.even.txt -g group.list -o AlphaRarefaction_Output/
# 输出目录：AlphaRarefaction_Output/；文件：rank_abundance.svg/png, observed_features.svg/png, alpha_diversity.svg/png, ...
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_alpha_rarefaction.sh -t asv_table.even.txt -g group.list -o AlphaRarefaction_Output/
# 输出目录：AlphaRarefaction_Output/；文件：rank_abundance.svg/png, observed_features.svg/png, alpha_diversity.svg/png, observed_features.group.svg/png, alpha_diversity.group.svg/png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -t, --table | 均一化 ASV 表路径 | 是 | - | asv_table.even.txt |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -o, --output | 输出目录 | 是 | - | AlphaRarefaction_Output/ |

---

## 流程步骤

```
1️⃣ color_defined.pl（自动生成 group_col.list 分组颜色配置）
   ↓
2️⃣ rank_abundance.R（绘制 Rank Abundance 曲线）
   ↓
3️⃣ alpha_rarefaction.pl（处理稀化曲线数据）
   ↓
4️⃣ plot_aplhaindex.R（绘制 Observed Features 曲线）
   ↓
5️⃣ convert（合并图片）
   ↓
6️⃣ rarefacton_group.py（分组稀化曲线）
   ↓
7️⃣ line_errbar.R（绘制分组误差线图）
   ↓
8️⃣ Combine_otutable.pl（按 group.list 生成分组 ASV 表）
   ↓
9️⃣ rank_abundance_group.R（绘制分组 Rank Abundance 曲线）
   ↓
🔟 convert（合并分组图片）
```

---

## group.list 格式

```
# 样本名\t分组名
Sample001\tGroupA
Sample002\tGroupA
Sample003\tGroupB
Sample004\tGroupB
```

**说明**：
- 第一列为样本名，第二列为分组名
- 制表符（Tab）分隔
- 分组颜色配置由脚本自动调用 `color_defined.pl` 生成（基于内置颜色表）

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **Rscript**: `/gfs/softwares/R/3.6.3/bin/Rscript`
- **perl**: `/usr/bin/perl`
- **python**: `/gfs/users/guorongjun/miniconda3/bin/python`
- **convert**: `/usr/bin/convert` (ImageMagick)
- **rank_abundance.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/rank_abundance.R`
- **alpha_rarefaction.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/alpha_rarefaction.pl`
- **plot_aplhaindex.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/plot_aplhaindex.R`
- **rarefacton_group.py**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/rarefacton_group.py`
- **line_errbar.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/line_errbar.R`
- **rank_abundance_group.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/rank_abundance_group.R`
- **Combine_otutable.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/Combine_otutable.pl`
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' > .env
echo 'export PERL_BIN="/your/path/to/perl"' >> .env
echo 'export PYTHON_BIN="/your/path/to/python"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
echo 'export RANK_ABUNDANCE_R="/your/path/to/rank_abundance.R"' >> .env
echo 'export ALPHA_RAREFACTION_PL="/your/path/to/alpha_rarefaction.pl"' >> .env
echo 'export PLOT_ALPHAINDEX_R="/your/path/to/plot_aplhaindex.R"' >> .env
echo 'export RAREFACTION_GROUP_PY="/your/path/to/rarefacton_group.py"' >> .env
echo 'export LINE_ERRBAR_R="/your/path/to/line_errbar.R"' >> .env
echo 'export RANK_ABUNDANCE_GROUP_R="/your/path/to/rank_abundance_group.R"' >> .env
echo 'export COMBINE_OTUTABLE_PL="/your/path/to/Combine_otutable.pl"' >> .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step5_alpha_rarefaction.sh ... -o AlphaRarefaction_Output/
```
---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt, group.list | 均一化 ASV 表与样本分组信息 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | alpha_diversity.png | 插入分析报告 |
| 报告生成 | alpha_diversity.group.png | 插入分组分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step5_alpha_rarefaction.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step5_alpha_rarefaction.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step5_alpha_rarefaction/`

---

最后更新：2026-06-24
