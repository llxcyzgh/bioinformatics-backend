# SIMPER - 相似性百分比分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | simper |
| **Description** | SIMPER（Similarity Percentage）分析，识别组间差异贡献最大的物种 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组差异物种筛选 |
| **估算机时** | 1.0 小时 |
| **报价分数** | 1.8 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative/ | 各分类层级相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_simper/Relative/) |
| asv_table.even.txt | 均一化 ASV 表（step3 输出，脚本内自动生成 Relative/） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_simper/asv_table.even.txt) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_simper/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| {level}/simper_*.txt | 各层级 SIMPER 分析结果 | TXT | 16S/18S/ITS | 通用 | - |
| {level}/*.pdf, {level}/*.png | 各层级 SIMPER 图 | PDF/PNG | 16S/18S/ITS | 通用 | - |

`{level}` 为所选分类层级目录名：`otu`、`phylum`、`class`、`order`、`family`、`genus`、`species`。

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_simper.sh -i Relative/ -g group.list -o Simper_Output/
# 或 -i TableStats/asv_table.even.txt（自动生成 Relative/）
# 默认分析全部层级：otu, phylum, class, order, family, genus, species
```

**示例 1**（Relative/ 目录，全部层级）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_simper.sh -i Relative/ -g group.list -o Simper_Output/
```

**示例 2**（均一化 ASV 表，自动生成 Relative/）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_simper.sh \
    -i asv_table.even.txt \
    -g group.list \
    -o Simper_Output/
```

**示例 3**（仅指定层级）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_simper.sh \
    -i Relative/ -g group.list \
    -l phylum,genus \
    -o Simper_Output/
# 等价于 -l p,g
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | Relative/ 目录或 asv_table.even.txt | 是 | - | Relative/ |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -l, --levels | 分析层级，逗号分隔 | 否 | 全部层级 | phylum,genus 或 p,g |
| --top | Top 物种数量 | 否 | 10 | 10 |
| -o, --output | 输出目录 | 是 | - | Simper_Output/ |

**可选层级**：`otu`、`phylum(p)`、`class(c)`、`order(o)`、`family(f)`、`genus(g)`、`species(s)`

---

## 流程步骤

```
0️⃣ （可选）stat_otu_tab.pl 由 asv_table.even.txt 生成 Relative/
   ↓
1️⃣ 按所选层级循环：simper.R（otu）或 simper.tax.R（各分类层级）
   ↓
2️⃣ 生成各层级 SIMPER 结果（simper_*.txt, *.pdf/png）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **stat_otu_tab.pl**: `/newVol/.../lib/03.ASV/featureAnalysis/stat_otu_tab.pl`
- **get.simper.pl / simper.R / simper.tax.R**: `/newVol/.../lib/04.Taxa_visualization/lib/simper/`
- **Rscript**: `/gfs/softwares/R/3.6.3/bin/Rscript`
- **convert**: `/usr/bin/convert`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export STAT_OTU_TAB_PL="/your/path/to/stat_otu_tab.pl"' >> .env
echo 'export GET_SIMPER_PL="/your/path/to/get.simper.pl"' >> .env
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' >> .env
source .env
bash step4_simper.sh ... -o Simper_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative/, asv_table.even.txt | 相对丰度表或均一化 ASV 表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | */simper_*.txt | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step4_simper.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step4_simper.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step4_simper/`

---

最后更新：2026-06-24
