# Top Species - Top10 物种与柱状图模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | top_species |
| **Description** | 筛选各分类层级 Top10 物种，绘制相对丰度柱状图 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组物种组成可视化 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|------|
| Relative/asv_table.*.relative.xls | 各分类层级相对丰度表 | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_top_species/Relative/asv_table.g.relative.xls) |
| group.list | 样本分组文件（可选） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_top_species/group.list) |

---

## 输出

> 所有输出文件均写入 `-o` 指定的目录（下表路径相对于输出目录）。

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| top10/asv_table.*10.relative.xls | 样本 Top10 物种表 | XLS | 16S/18S/ITS | 通用 | - |
| top10/*10.relative.dis.png | 样本 Top10 柱状图 | PNG | 16S/18S/ITS | 通用 | - |
| top10_group/asv_table.*10.group.relative.xls | 分组 Top10 物种表（提供 group.list 时） | XLS | 16S/18S/ITS | 通用 | - |
| top10_group/*10.group.relative.dis.png | 分组 Top10 柱状图（提供 group.list 时） | PNG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_top_species.sh -i <Relative/> -o TopSpecies_Output/
# 输出目录：TopSpecies_Output/；文件：top10/*.xls, top10/*.png
```

**示例 1**：样本 Top10
```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_top_species.sh" \
    -i TableStats_Output/Relative/ \
    -o TopSpecies_Output/
```

**示例 2**：样本 + 分组 Top10
```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_top_species.sh" \
    -i TableStats_Output/Relative/ \
    -g group.list \
    -o TopSpecies_Output/
# 输出：top10/asv_table.*10.relative.xls, top10_group/asv_table.*10.group.relative.xls, ...
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 相对丰度表目录（含 `*.relative.xls`） | 是 | - | TableStats_Output/Relative/ |
| -g, --group | 样本分组文件路径 | 否 | - | group.list |
| -o, --output | 输出目录 | 是 | - | TopSpecies_Output/ |

---

## 流程步骤

```
1️⃣ 读取 -i 指定的相对丰度表目录
   ↓
2️⃣ 筛选各层级样本 Top10 → 输出到 top10/
   ↓
3️⃣ 格式转换 (tran_tab.pl)
   ↓
4️⃣ 绘制样本柱状图 (bar_diagram.pl) + SVG → PNG
   ↓
5️⃣ 分组 Top10（提供 group.list 时）
   ├─ Combine_table.pl（样本 Top10 → 分组汇总）
   ├─ tran_tab.pl
   └─ bar_diagram.pl + svg2xxx（x_title: Group Name）
```

---

## 输出文件说明

### 样本 Top10 物种表（top10/）
每个分类层级的丰度最高的 10 个物种：
- `top10/asv_table.k10.relative.xls` - 界水平 Top10
- `top10/asv_table.p10.relative.xls` - 门水平 Top10
- `top10/asv_table.c10.relative.xls` - 纲水平 Top10
- `top10/asv_table.o10.relative.xls` - 目水平 Top10
- `top10/asv_table.f10.relative.xls` - 科水平 Top10
- `top10/asv_table.g10.relative.xls` - 属水平 Top10
- `top10/asv_table.s10.relative.xls` - 种水平 Top10

### 样本柱状图（top10/）
每个分类层级 Top10 物种的相对丰度柱状图（PNG 格式）：
- `top10/k10.relative.dis.png` - 界水平 Top10
- `top10/p10.relative.dis.png` - 门水平 Top10
- `top10/c10.relative.dis.png` - 纲水平 Top10
- `top10/o10.relative.dis.png` - 目水平 Top10
- `top10/f10.relative.dis.png` - 科水平 Top10
- `top10/g10.relative.dis.png` - 属水平 Top10
- `top10/s10.relative.dis.png` - 种水平 Top10

### 分组 Top10（提供 group.list 时）
输出目录 `top10_group/`：
- `asv_table.g10.group.relative.xls` - 属水平分组 Top10
- `g10.group.relative.dis.png` - 属水平分组 Top10 柱状图
- 其余层级（k/p/c/o/f/s）同理

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **get_table_head2.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/get_table_head2.pl`
- **tran_tab.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/tran_tab.pl`
- **bar_diagram.pl**: `.../00.Commbin/bar_diagram.pl`
- **Combine_table.pl**: `.../00.Commbin/test_bin/Combine_table.pl`
- **svg2xxx**: `.../software/svg2xxx_release/svg2xxx`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export GET_TABLE_HEAD2_PL="/your/path/to/get_table_head2.pl"' >> .env
echo 'export TRAN_TAB_PL="/your/path/to/tran_tab.pl"' >> .env
echo 'export BAR_DIAGRAM_PL="/your/path/to/bar_diagram.pl"' >> .env
echo 'export SVG2XXX_BIN="/your/path/to/svg2xxx"' >> .env
source .env
bash step3_top_species.sh ... -o TopSpecies_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative/*.relative.xls, group.list | 相对丰度表与分组信息 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step4_otutree | top10/asv_table.p10.relative.xls | 样本 OTU 树（配合 step3_upgma 样本 .tre） |
| step4_otutree | top10_group/asv_table.p10.group.relative.xls | 分组 OTU 树（配合 step3_upgma 分组 .tre） |
| step4_taxa | top10/*.png, top10_group/*.png | 物种组成可视化 |
| 报告生成 | top10/*.png, top10_group/*.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step3_top_species.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step3_top_species.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step3_top_species/`

---

最后更新：2026-06-24
