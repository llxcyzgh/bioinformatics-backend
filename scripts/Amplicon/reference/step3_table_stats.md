# Table Stats - ASV 表均一化与相对丰度模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | table_stats |
| **Description** | ASV 特征表均一化处理，计算各分类层级相对丰度 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组组成分析 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|------|
| asv_table.txt | 标准化 ASV 特征表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_table_stats/asv_table.txt) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化后的 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_alpha_data/asv_table.even.txt) |
| Relative/asv_table.*.relative.xls | 各分类层级相对丰度表 | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_top_species/Relative/asv_table.g.relative.xls) |

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_table_stats.sh -i asv_table.txt
# 输出：asv_table.even.txt, Relative/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | ASV 表文件路径 | 是 | - | asv_table.txt |

---

## 流程步骤

```
1️⃣ 数据均一化 (stat_otu_tab.pl --even)
   ↓
2️⃣ 计算相对丰度 (stat_otu_tab.pl --prefix)
   ↓
输出：asv_table.even.txt + Relative/各层级相对丰度表
```

---

## 输出文件说明

### 均一化文件
- `asv_table.even.txt` - 均一化到相同测序深度的 ASV 表（用于 Alpha/Beta 多样性分析）

### 相对丰度目录 (Relative/)
按分类层级（k/p/c/o/f/g/s）的相对丰度表：
- `asv_table.k.relative.xls` - 界水平
- `asv_table.p.relative.xls` - 门水平
- `asv_table.c.relative.xls` - 纲水平
- `asv_table.o.relative.xls` - 目水平
- `asv_table.f.relative.xls` - 科水平
- `asv_table.g.relative.xls` - 属水平
- `asv_table.s.relative.xls` - 种水平

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **stat_otu_tab.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export STAT_OTU_TAB_PL="/your/path/to/stat_otu_tab.pl"' >> .env
source .env
bash step3_table_stats.sh ...
```
---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_feature_tables | asv_table.txt | 标准化 ASV 特征表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step3_top_species | Relative/*.relative.xls | Top10 物种 + 柱状图 |
| step4_alpha | asv_table.even.txt | Alpha 多样性分析 |
| step4_beta | asv_table.even.txt | Beta 多样性分析 |
| step4_taxa | Relative/*.relative.xls | 物种组成分析 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step3_table_stats.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step3_table_stats.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step3_table_stats/`

---

最后更新：2026-04-15
