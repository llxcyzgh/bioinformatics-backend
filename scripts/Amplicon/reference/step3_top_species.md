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
| Relative/asv_table.*.relative.xls | 各分类层级相对丰度表 | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_top_species/Relative/asv_table.g.relative.xls) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| top10/asv_table.*10.relative.xls | Top10 物种表 | XLS | 16S/18S/ITS | 通用 | - |
| top10/*10.relative.dis.png | Top10 柱状图 | PNG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_top_species.sh
# 输出：top10/*.xls, top10/*.png
```

**示例**：
```bash
cd /path/to/project/03.Make_ASV/Table_Stats
bash "${AMPLICON_ROOT}/scripts/step3_top_species.sh"
# 输出：top10/asv_table.*10.relative.xls, top10/*10.relative.dis.png
```

### 参数说明

此脚本无需参数，自动从当前目录读取 `Relative/` 下的相对丰度表。

---

## 流程步骤

```
1️⃣ 读取 Relative/下的相对丰度表
   ↓
2️⃣ 筛选各层级 Top10 物种 (get_table_head2.pl)
   ↓
3️⃣ 格式转换 (tran_tab.pl)
   ↓
4️⃣ 绘制柱状图 (bar_diagram.pl)
   ↓
5️⃣ SVG → PNG 转换 (svg2xxx)
```

---

## 输出文件说明

### Top10 物种表
每个分类层级的丰度最高的 10 个物种：
- `asv_table.k10.relative.xls` - 界水平 Top10
- `asv_table.p10.relative.xls` - 门水平 Top10
- `asv_table.c10.relative.xls` - 纲水平 Top10
- `asv_table.o10.relative.xls` - 目水平 Top10
- `asv_table.f10.relative.xls` - 科水平 Top10
- `asv_table.g10.relative.xls` - 属水平 Top10
- `asv_table.s10.relative.xls` - 种水平 Top10

### 柱状图
每个分类层级 Top10 物种的相对丰度柱状图（PNG 格式）：
- `k10.relative.dis.png` - 界水平 Top10
- `p10.relative.dis.png` - 门水平 Top10
- `c10.relative.dis.png` - 纲水平 Top10
- `o10.relative.dis.png` - 目水平 Top10
- `f10.relative.dis.png` - 科水平 Top10
- `g10.relative.dis.png` - 属水平 Top10
- `s10.relative.dis.png` - 种水平 Top10

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **get_table_head2.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/get_table_head2.pl`
- **tran_tab.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/tran_tab.pl`
- **bar_diagram.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/bar_diagram.pl`
- **svg2xxx**: `/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx`

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
bash step3_top_species.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative/*.relative.xls | 各层级相对丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step4_taxa | top10/*.png | 物种组成可视化 |
| 报告生成 | top10/*.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step3_top_species.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step3_top_species.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step3_top_species/`

---

最后更新：2026-04-15
