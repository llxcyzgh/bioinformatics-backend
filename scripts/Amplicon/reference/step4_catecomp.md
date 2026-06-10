# Catecomp - 分类比较统计检验模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | catecomp |
| **Description** | 分类比较统计检验，包括 ANOSIM、MRPP、Adonis、AMOVA 等多种统计方法 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Beta 多样性统计检验 |
| **估算机时** | 1.0 小时 |
| **报价分数** | 1.8 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_catecomp/asv_table.even.txt) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_catecomp/group.list) |
| unweighted_unifrac_dm.txt | Unweighted UniFrac 距离矩阵 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_catecomp/unweighted_unifrac_dm.txt) |
| weighted_unifrac_dm.txt | Weighted UniFrac 距离矩阵 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_catecomp/weighted_unifrac_dm.txt) |

**注**：距离矩阵文件为可选输入，如不提供则跳过相关分析。

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Anosim/stat_anosim.txt | ANOSIM 统计结果 | TXT | 16S/18S/ITS | 通用 | - |
| Anosim/stat_anosim.js | ANOSIM 交互网页 | JS | 16S/18S/ITS | 通用 | - |
| MRPP/stat_mrpp.txt | MRPP 统计结果 | TXT | 16S/18S/ITS | 通用 | - |
| MRPP/stat_mrpp.js | MRPP 交互网页 | JS | 16S/18S/ITS | 通用 | - |
| Adonis/bray_adonis.txt | Adonis (PERMANOVA) 结果 | TXT | 16S/18S/ITS | 通用 | - |
| Adonis/stat_adonis.js | Adonis 交互网页 | JS | 16S/18S/ITS | 通用 | - |
| Amova/weighted_unifrac/stat_amova.txt | AMOVA 统计结果 | TXT | 16S/18S/ITS | 通用 | - |
| Amova/weighted_unifrac/stat_amova.js | AMOVA 交互网页 | JS | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_catecomp.sh -t asv_table.even.txt -g group.list [-u unweighted_unifrac_dm.txt] [-w weighted_unifrac_dm.txt]
# 输出：Anosim/, MRPP/, Adonis/, Amova/
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_catecomp.sh -t asv_table.even.txt -g group.list -u unweighted_unifrac_dm.txt -w weighted_unifrac_dm.txt
# 输出：Anosim/stat_anosim.txt, MRPP/stat_mrpp.txt, Adonis/bray_adonis.txt, Amova/stat_amova.txt
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -t, --table | 均一化 ASV 表路径 | 是 | - | asv_table.even.txt |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -u, --unweighted | Unweighted UniFrac 距离矩阵路径 | 否 | - | unweighted_unifrac_dm.txt |
| -w, --weighted | Weighted UniFrac 距离矩阵路径 | 否 | - | weighted_unifrac_dm.txt |

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
- 分组颜色配置由脚本自动生成（基于内置颜色表）

---

## 流程步骤

```
1️⃣ 读取 ASV 表和 group.list
   ↓
2️⃣ 自动生成 group_col.list（分组颜色配置）
   ↓
3️⃣ Categorise_compair.pl（执行 ANOSIM、MRPP、Adonis、AMOVA）
   ↓
4️⃣ tab_js.pl（生成各统计方法的交互网页）
   ↓
5️⃣ 输出统计结果和 JS 文件
```

---

## 统计方法说明

| 方法 | 全称 | 用途 |
|------|------|------|
| **ANOSIM** | Analysis of Similarities | 分析组间差异是否显著大于组内差异 |
| **MRPP** | Multi-Response Permutation Procedure | 多响应置换过程，检验组间差异 |
| **Adonis** | PERMANOVA | 基于距离矩阵的方差分析 |
| **AMOVA** | Analysis of Molecular Variance | 分子方差分析（需要进化距离） |

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **Categorise_compair.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Categorise_compair/Categorise_compair.pl`
- **tab_js.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/tab_js.pl`
- **colors.txt**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/colors.txt`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export CATEGORISE_COMPAIR_PL="/your/path/to/Categorise_compair.pl"' >> .env
echo 'export TAB_JS_PL="/your/path/to/tab_js.pl"' >> .env
echo 'export COLORS_FILE="/your/path/to/colors.txt"' >> .env
source .env
bash step4_catecomp.sh ...
```
---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt | 均一化 ASV 表 |
| step3_table_stats | group.list | 样本分组信息 |
| step3_beta_data | unweighted_unifrac_dm.txt | Unweighted UniFrac 距离矩阵 |
| step3_beta_data | weighted_unifrac_dm.txt | Weighted UniFrac 距离矩阵 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | Anosim/stat_anosim.txt | 插入分析报告 |
| 报告生成 | MRPP/stat_mrpp.txt | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_catecomp.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_catecomp.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_catecomp/`

---

最后更新：2026-04-15
