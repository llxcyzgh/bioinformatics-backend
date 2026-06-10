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
| asv_table.relative.xls | 相对丰度 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step5_pca/asv_table.relative.xls) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step5_pca/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| UOA_pca.svg | PCA 排序图（SVG 格式） | SVG | 16S/18S/ITS | 通用 | - |
| UOA_pca.pdf | PCA 排序图（PDF 格式） | PDF | 16S/18S/ITS | 通用 | - |
| UOA_pca.png | PCA 排序图（PNG 格式） | PNG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step5_pca.sh -r asv_table.relative.xls -g group.list
# 输出：UOA_pca.svg, UOA_pca.pdf, UOA_pca.png
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step5_pca.sh -r asv_table.relative.xls -g group.list
# 输出：UOA_pca.svg, UOA_pca.pdf, UOA_pca.png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -r, --relative | 相对丰度 ASV 表路径 | 是 | - | asv_table.relative.xls |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |

---

## 流程步骤

```
1️⃣ color_defined.pl（自动生成 group_col.list 分组颜色配置）
   ↓
2️⃣ UOA.R（绘制 PCA 排序图）
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
echo 'export UOA_R_PL="/your/path/to/UOA.R"' >> .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step5_pca.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.relative.xls | 相对丰度 ASV 表 |
| step3_table_stats | group.list | 样本分组信息 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | UOA_pca.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step5_pca.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step5_pca.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step5_pca/`

---

最后更新：2026-04-16
