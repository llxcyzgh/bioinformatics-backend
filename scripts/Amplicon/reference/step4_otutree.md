# OTU Tree - 物种进化树可视化模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | otutree |
| **Description** | 基于 UPGMA 树和 Top10 物种丰度绘制带丰度信息的进化树 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组物种进化关系可视化 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| upgma_tree.tre | UPGMA 系统发育树 | TRE | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_otutree/upgma_tree.tre) |
| top10_asv_table.p.relative.xls | 门水平 Top10 物种丰度表 | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_otutree/top10_asv_table.p.relative.xls) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| UPGMA.W.tree.svg | Weighted UniFrac 树（SVG） | SVG | 16S/18S/ITS | 通用 | - |
| UPGMA.W.tree.png | Weighted UniFrac 树（PNG） | PNG | 16S/18S/ITS | 通用 | - |
| UPGMA.UnW.tree.svg | Unweighted UniFrac 树（SVG） | SVG | 16S/18S/ITS | 通用 | - |
| UPGMA.UnW.tree.png | Unweighted UniFrac 树（PNG） | PNG | 16S/18S/ITS | 通用 | - |

---

## 执行命令


**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_otutree.sh -t upgma_tree.tre -r top10_asv_table.p.relative.xls
# 输出：UPGMA.W.tree.svg/png, UPGMA.UnW.tree.svg/png
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_otutree.sh -t upgma_tree.tre -r top10_asv_table.p.relative.xls
# 输出：UPGMA.W.tree.svg, UPGMA.W.tree.png, UPGMA.UnW.tree.svg, UPGMA.UnW.tree.png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -t, --tree | UPGMA 树文件路径 | 是 | - | upgma_tree.tre |
| -r, --relative | Top10 物种丰度表路径 | 是 | - | top10_asv_table.p.relative.xls |

---

## 流程步骤

```
1️⃣ draw_tree.pl（绘制 Weighted UniFrac 树）
   ↓
2️⃣ svg2xxx（SVG → PNG 转换）
   ↓
3️⃣ draw_tree.pl（绘制 Unweighted UniFrac 树）
   ↓
4️⃣ svg2xxx（SVG → PNG 转换）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **draw_tree.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/draw_tree.pl`
- **svg2xxx**: `/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export DRAW_TREE_PL="/your/path/to/draw_tree.pl"' >> .env
echo 'export SVG2XXX_BIN="/your/path/to/svg2xxx"' >> .env
source .env
bash step4_otutree.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_upgma | upgma_tree.tre | UPGMA 系统发育树 |
| step3_top_species | top10_asv_table.p.relative.xls | 门水平 Top10 物种表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | UPGMA.W.tree.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_otutree.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_otutree.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_otutree/`

---

最后更新：2026-04-15
