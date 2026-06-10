# Alpha Div - Alpha 多样性差异分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | alpha_div |
| **Description** | Alpha 多样性差异分析，包括 ANOVA 检验和 Beeswarm 图可视化 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Alpha 多样性差异比较 |
| **估算机时** | 1.0 小时 |
| **报价分数** | 1.8 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| alpha_diversity_index.txt | Alpha 多样性指数表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step5_alpha_div/alpha_diversity_index.txt) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step5_alpha_div/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| anova_test.txt | ANOVA 检验结果 | TXT | 16S/18S/ITS | 通用 | - |
| beeswarm/observed_features.svg/png | Observed Features 蜜蜂群图 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| beeswarm/shannon.svg/png | Shannon 指数蜜蜂群图 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| alpha_diff.svg/png | Alpha 多样性差异合并图 | SVG/PNG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step5_alpha_div.sh -i alpha_diversity_index.txt -g group.list
# 输出：anova_test.txt, beeswarm/, alpha_diff.svg/png
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step5_alpha_div.sh -i alpha_diversity_index.txt -g group.list
# 输出：anova_test.txt, beeswarm/observed_features.svg/png, beeswarm/shannon.svg/png, alpha_diff.svg/png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | Alpha 多样性指数表路径 | 是 | - | alpha_diversity_index.txt |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |

---

## 流程步骤

```
1️⃣ color_defined.pl（自动生成 group_col.list 分组颜色配置）
   ↓
2️⃣ Alpha_div_anova_test.pl（ANOVA 检验）
   ↓
3️⃣ beeswarm.pl（绘制 Observed Features 蜜蜂群图）
   ↓
4️⃣ beeswarm.pl（绘制 Shannon 指数蜜蜂群图）
   ↓
5️⃣ convert（合并图片）
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
- **perl**: `/usr/bin/perl`
- **convert**: `/usr/bin/convert` (ImageMagick)
- **Alpha_div_anova_test.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_div/Alpha_div_anova_test.pl`
- **beeswarm.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_div/beeswarm.pl`
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
echo 'export ALPHA_DIV_ANOVA_TEST_PL="/your/path/to/Alpha_div_anova_test.pl"' >> .env
echo 'export BEESWARM_PL="/your/path/to/beeswarm.pl"' >> .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step5_alpha_div.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step5_alpha_rarefaction | alpha_diversity_index.txt | Alpha 多样性指数表 |
| step3_table_stats | group.list | 样本分组信息 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | alpha_diff.png | 插入分析报告 |
| 报告生成 | anova_test.txt | 插入统计结果 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step5_alpha_div.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step5_alpha_div.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step5_alpha_div/`

---

最后更新：2026-04-16
