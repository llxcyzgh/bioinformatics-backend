# PCoA - 主坐标分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | pcoa |
| **Description** | PCoA（Principal Co-ordinates Analysis）主坐标分析，基于 Beta 多样性距离展示样本间的群落结构差异 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Beta 多样性排序分析 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| BetaData/ | step3_beta_data 输出目录（含 *_pcoa_results_qza/ordination.txt） | DIR | 16S/18S/ITS | 通用 | - |
| ordination.txt | 单个距离的 PCoA ordination 文件 | TXT | 16S/18S/ITS | 通用 | unweighted_unifrac_pcoa_results_qza/ordination.txt |
| *_pc.txt | 已整理的 PC 坐标（兼容旧用法） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_pcoa/BetaData/weighted_unifrac_pcoa_results_qza/ordination.txt) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_pcoa/group.list) |

---

## 输出

> 所有输出文件均写入 `-o` 指定的目录（下表路径相对于输出目录）。

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| {distance}/PCoA12.pdf | 各距离 PCoA 排序图 | PDF | 16S/18S/ITS | 通用 | weighted_unifrac/PCoA12.pdf |
| {distance}/PCoA12.png | 各距离 PCoA 排序图 | PNG | 16S/18S/ITS | 通用 | weighted_unifrac/PCoA12.png |
| {distance}/{distance}_pc.txt | 由 ordination.txt 导出的 PC 坐标 | TSV | 16S/18S/ITS | 通用 | weighted_unifrac/weighted_unifrac_pc.txt |

`{distance}` 为所选距离：`unweighted_unifrac`、`weighted_unifrac`、`jaccard`、`bray_curtis`。各距离结果直接位于输出目录下以距离名命名的子目录中。

---

## 执行命令

### 调用脚本 (推荐)

**示例 1**（BetaData 目录，默认 Weighted + Unweighted UniFrac）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh \
    -i BetaData/ \
    -g group.list \
    -o PCoA_Output/
```

**示例 2**（选择特定距离）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh \
    -i BetaData/ \
    -d weighted_unifrac,jaccard \
    -g group.list \
    -o PCoA_Output/
# 等价于 -d w,j
```

**示例 3**（单个 ordination.txt）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh \
    -i BetaData/unweighted_unifrac_pcoa_results_qza/ordination.txt \
    -g group.list \
    -o PCoA_Output/
```

**示例 4**（兼容旧用法：直接传入 pc 坐标文件）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh \
    -w weighted_unifrac_pc.txt \
    -wu unweighted_unifrac_pc.txt \
    -g group.list \
    -o PCoA_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | BetaData/ 目录或 ordination.txt | 与 -w/-wu 二选一 | - | BetaData/ |
| -d, --distances | 距离类型，逗号分隔 | 否 | unweighted_unifrac,weighted_unifrac | w,j |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -w, --weighted | weighted_unifrac_pc.txt（旧用法） | 否 | - | weighted_unifrac_pc.txt |
| -wu, --unweighted | unweighted_unifrac_pc.txt（旧用法） | 否 | - | unweighted_unifrac_pc.txt |
| -o, --output | 输出目录 | 是 | - | PCoA_Output/ |

**可选距离**：`unweighted_unifrac(wu)`、`weighted_unifrac(w)`、`jaccard(j)`、`bray_curtis(bc)`

---

## 流程步骤

```
0️⃣ color_defined.pl（由 group.list 自动生成 group_col.list）
   ↓
1️⃣ pcoa.pl（从 ordination.txt 导出 {distance}_pc.txt）
   ↓
2️⃣ plot_PCoA.R（在各距离目录下绘制 PCoA 图）
   ↓
3️⃣ convert（PDF → PNG 转换，各距离目录内）
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

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **Rscript**: `/gfs/softwares/R/3.6.3/bin/Rscript`
- **convert**: `/usr/bin/convert` (ImageMagick)
- **perl**: `/usr/bin/perl`
- **pcoa.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/betaAnalysis/pcoa.pl`
- **plot_PCoA.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCoA/plot_PCoA.R`
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`

### 自定义路径（迁移环境时）

```bash
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' > .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
echo 'export PERL_BIN="/your/path/to/perl"' >> .env
echo 'export PCOA_PL="/your/path/to/pcoa.pl"' >> .env
echo 'export PCOA_R_PL="/your/path/to/plot_PCoA.R"' >> .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step5_pcoa.sh ... -o PCoA_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_beta_data | BetaData/*_pcoa_results_qza/ordination.txt | PCoA ordination 坐标 |
| step3_upgma | PCoA_data/*_pc.txt | PC 坐标（可选，旧流程） |
| step3_table_stats | group.list | 样本分组信息 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | PCoA.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step5_pcoa.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step5_pcoa/`

---

最后更新：2026-06-24
