# NMDS - 非度量多维尺度分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | nmds |
| **Description** | NMDS（Non-metric Multidimensional Scaling）非度量多维尺度分析，展示样本间的群落结构差异 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Beta 多样性排序分析 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化 ASV 表（脚本内自动生成 Relative/） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_nmds/asv_table.even.txt) |
| Relative/ | 各分类层级相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_nmds/Relative/) |
| asv_table.*.relative.xls | 单层级相对丰度表 | XLS | 16S/18S/ITS | 通用 | asv_table.g.relative.xls |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_nmds/group.list) |
| group_col.list | 分组颜色配置（可选，默认由 group.list 自动生成） | TSV | 16S/18S/ITS | 通用 | - |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| NMDS.png/pdf/svg | 单层级 NMDS 排序图 | PNG/PDF/SVG | 16S/18S/ITS | 通用 | - |
| NMDS.{level}.png/pdf | 多层级 NMDS 排序图 | PNG/PDF | 16S/18S/ITS | 通用 | NMDS.g.png |
| Relative/ | 由 asv_table.even.txt 生成的相对丰度表（可选） | DIR | 16S/18S/ITS | 通用 | - |

`{level}` 为分类层级代码：`k`、`p`、`c`、`o`、`f`、`g`、`s`、`otu`。

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh -i asv_table.even.txt -g group.list -o NMDS_Output/
# 默认属水平（genus）；多层级：-l phylum,genus
```

**示例 1**（均一化 ASV 表，自动生成 Relative 并做属水平 NMDS）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh \
    -i TableStats/asv_table.even.txt \
    -g group.list \
    -o NMDS_Output/
```

**示例 2**（已有 Relative/ 目录，分析多个层级）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh \
    -i TableStats/Relative/ \
    -g group.list \
    -l phylum,genus,species \
    -o NMDS_Output/
```

**示例 3**（直接指定相对丰度表）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh \
    -i TableStats/Relative/asv_table.g.relative.xls \
    -g group.list \
    -o NMDS_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | asv_table.even.txt、Relative/ 或 *.relative.xls | 是 | - | asv_table.even.txt |
| -t, --table | 同 -i（均一化 ASV 表） | 是* | - | asv_table.even.txt |
| -r, --relative | 同 -i（Relative/ 或相对丰度表） | 是* | - | Relative/asv_table.g.relative.xls |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -l, --levels | 分析层级，逗号分隔 | 否 | genus | phylum,genus 或 p,g |
| -c, --color | 分组颜色配置文件路径 | 否 | 由 group.list 自动生成 | group_col.list |
| -o, --output | 输出目录 | 是 | - | NMDS_Output/ |

\* `-i`、`-t`、`-r` 三选一即可。

**可选层级**：`kingdom(k)`、`phylum(p)`、`class(c)`、`order(o)`、`family(f)`、`genus(g)`、`species(s)`、`otu(asv)`

---

## 流程步骤

```
0️⃣（可选）stat_otu_tab.pl 生成 Relative/（-i 为 asv_table.even.txt 时）
   ↓
0️⃣ color_defined.pl（未提供 -c 时，由 group.list 自动生成 group_col.list）
   ↓
1️⃣ NMDS.R.pl（按所选层级绘制 NMDS 排序图）
   ↓
2️⃣ convert（PDF → PNG 转换）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **stat_otu_tab.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl`
- **convert**: `/usr/bin/convert` (ImageMagick)
- **NMDS.R.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/NMDS/NMDS.R.pl`
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export STAT_OTU_TAB_PL="/your/path/to/stat_otu_tab.pl"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
echo 'export NMDS_R_PL="/your/path/to/NMDS.R.pl"' >> .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step5_nmds.sh ... -o NMDS_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt, Relative/, group.list | 均一化表与相对丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | NMDS.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step5_nmds.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step5_nmds/`

---

最后更新：2026-06-24
