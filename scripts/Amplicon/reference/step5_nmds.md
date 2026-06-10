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
| asv_table.even.txt | 均一化 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step5_nmds/asv_table.even.txt) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step5_nmds/group.list) |
| group_col.list | 分组颜色配置 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step5_nmds/group_col.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| NMDS.svg | NMDS 排序图（SVG 格式） | SVG | 16S/18S/ITS | 通用 | - |
| NMDS.pdf | NMDS 排序图（PDF 格式） | PDF | 16S/18S/ITS | 通用 | - |
| NMDS.png | NMDS 排序图（PNG 格式） | PNG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step5_nmds.sh -t asv_table.even.txt -g group.list -c group_col.list
# 输出：NMDS.svg, NMDS.pdf, NMDS.png
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step5_nmds.sh -t asv_table.even.txt -g group.list -c group_col.list
# 输出：NMDS.svg, NMDS.pdf, NMDS.png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -t, --table | 均一化 ASV 表路径 | 是 | - | asv_table.even.txt |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -c, --color | 分组颜色配置文件路径 | 否 | - | group_col.list |

---

## 流程步骤

```
1️⃣ NMDS.R.pl（绘制 NMDS 排序图）
   ↓
2️⃣ convert（PDF → PNG 转换）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **convert**: `/usr/bin/convert` (ImageMagick)
- **NMDS.R.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/NMDS/NMDS.R.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
echo 'export NMDS_R_PL="/your/path/to/NMDS.R.pl"' >> .env
source .env
bash step5_nmds.sh ...
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
| 报告生成 | NMDS.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step5_nmds.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step5_nmds.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step5_nmds/`

---

最后更新：2026-04-15
