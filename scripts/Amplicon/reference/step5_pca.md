# PCA - 主成分分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | pca |
| **Description** | PCA（Principal Component Analysis）主成分分析，展示样本间的群落结构差异 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Beta 多样性排序分析 |
| **估算机时** | 1.0 小时 |
| **报价分数** | 1.8 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化 ASV 表（脚本内自动生成 Relative/） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_pca/asv_table.even.txt) |
| Relative/ | 各分类层级相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_pca/Relative/) |
| asv_table.*.relative.xls | 单层级相对丰度表 | XLS | 16S/18S/ITS | 通用 | asv_table.g.relative.xls |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_pca/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| UOA_pca.png/pdf/svg | 单层级 PCA 排序图 | PNG/PDF/SVG | 16S/18S/ITS | 通用 | - |
| UOA_pca.{level}.png/pdf | 多层级 PCA 排序图 | PNG/PDF | 16S/18S/ITS | 通用 | UOA_pca.g.png |
| Relative/ | 由 asv_table.even.txt 生成的相对丰度表（可选） | DIR | 16S/18S/ITS | 通用 | - |

`{level}` 为分类层级代码：`k`、`p`、`c`、`o`、`f`、`g`、`s`、`otu`。

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pca.sh -i asv_table.even.txt -g group.list -o PCA_Output/
# 默认属水平（genus）；多层级：-l phylum,genus
```

**示例 1**（均一化 ASV 表，自动生成 Relative 并做属水平 PCA）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pca.sh \
    -i TableStats/asv_table.even.txt \
    -g group.list \
    -o PCA_Output/
```

**示例 2**（已有 Relative/ 目录，分析多个层级）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pca.sh \
    -i TableStats/Relative/ \
    -g group.list \
    -l phylum,genus,species \
    -o PCA_Output/
```

**示例 3**（直接指定相对丰度表）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pca.sh \
    -i TableStats/Relative/asv_table.g.relative.xls \
    -g group.list \
    -o PCA_Output/
```

**示例 4**（兼容旧参数 `-r`）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pca.sh \
    -r asv_table.relative.xls \
    -g group.list \
    -o PCA_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | asv_table.even.txt、Relative/ 或 *.relative.xls | 是 | - | asv_table.even.txt |
| -t, --table | 同 -i（均一化 ASV 表） | 是* | - | asv_table.even.txt |
| -r, --relative | 同 -i（Relative/ 或相对丰度表） | 是* | - | Relative/asv_table.g.relative.xls |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -l, --levels | 分析层级，逗号分隔 | 否 | genus | phylum,genus 或 p,g |
| -o, --output | 输出目录 | 是 | - | PCA_Output/ |

\* `-i`、`-t`、`-r` 三选一即可。

**可选层级**：`kingdom(k)`、`phylum(p)`、`class(c)`、`order(o)`、`family(f)`、`genus(g)`、`species(s)`、`otu(asv)`

---

## 流程步骤

```
0️⃣（可选）stat_otu_tab.pl 生成 Relative/（-i 为 asv_table.even.txt 时）
   ↓
1️⃣ color_defined.pl（由 group.list 自动生成 group_col.list）
   ↓
2️⃣ UOA.R（按所选层级绘制 PCA 排序图）
   ↓
3️⃣ convert（PDF → PNG 转换）
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
- **convert**: `/usr/bin/convert` (ImageMagick)
- **perl**: `/usr/bin/perl`
- **stat_otu_tab.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl`
- **UOA.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCA/UOA.R`
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' > .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
echo 'export PERL_BIN="/your/path/to/perl"' >> .env
echo 'export STAT_OTU_TAB_PL="/your/path/to/stat_otu_tab.pl"' >> .env
echo 'export UOA_R_PL="/your/path/to/UOA.R"' >> .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step5_pca.sh ... -o PCA_Output/
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
| 报告生成 | UOA_pca.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step5_pca.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step5_pca.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step5_pca/`

---

最后更新：2026-06-24
