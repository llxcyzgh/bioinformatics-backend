# Beta Div - Beta 多样性差异分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | beta_div |
| **Description** | Beta 多样性差异分析，基于 UniFrac 距离矩阵进行组间差异统计检验 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Beta 多样性差异比较 |
| **估算机时** | 2.0 小时 |
| **报价分数** | 3.6 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| unweighted_unifrac_dm.txt | Unweighted UniFrac 距离矩阵 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_beta_div/unweighted_unifrac_dm.txt) |
| weighted_unifrac_dm.txt | Weighted UniFrac 距离矩阵 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_beta_div/weighted_unifrac_dm.txt) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step5_beta_div/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| unweighted_unifrac.svg/png | Unweighted UniFrac 差异箱线图 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| weighted_unifrac.svg/png | Weighted UniFrac 差异箱线图 | SVG/PNG | 16S/18S/ITS | 通用 | - |
| beta_diff.svg/png | Beta 多样性差异合并图 | SVG/PNG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_beta_div.sh -u unweighted_unifrac_dm.txt -w weighted_unifrac_dm.txt -g group.list -o BetaDiv_Output/
# 输出目录：BetaDiv_Output/；文件：unweighted_unifrac.svg/png, weighted_unifrac.svg/png, beta_diff.svg/png
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step5_beta_div.sh -u unweighted_unifrac_dm.txt -w weighted_unifrac_dm.txt -g group.list -o BetaDiv_Output/
# 输出目录：BetaDiv_Output/；文件：unweighted_unifrac.svg/png, weighted_unifrac.svg/png, beta_diff.svg/png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -u, --unweighted | Unweighted UniFrac 距离矩阵路径 | 是 | - | unweighted_unifrac_dm.txt |
| -w, --weighted | Weighted UniFrac 距离矩阵路径 | 是 | - | weighted_unifrac_dm.txt |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -o, --output | 输出目录 | 是 | - | BetaDiv_Output/ |

---

## 流程步骤

```
1️⃣ color_defined.pl（自动生成 group_col.list 分组颜色配置）
   ↓
2️⃣ Beta_group_test.pl（Unweighted UniFrac 组间差异检验）
   ↓
3️⃣ Beta_group_test.pl（Weighted UniFrac 组间差异检验）
   ↓
4️⃣ convert（合并图片）
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
- **Beta_group_test.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Beta_div/Beta_group_test.pl`
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
echo 'export BETA_GROUP_TEST_PL="/your/path/to/Beta_group_test.pl"' >> .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step5_beta_div.sh ... -o BetaDiv_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_beta_data | unweighted_unifrac_dm.txt | Unweighted UniFrac 距离矩阵 |
| step3_beta_data | weighted_unifrac_dm.txt | Weighted UniFrac 距离矩阵 |
| step3_table_stats | group.list | 样本分组信息 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | beta_diff.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step5_beta_div.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step5_beta_div.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step5_beta_div/`

---

最后更新：2026-06-24
