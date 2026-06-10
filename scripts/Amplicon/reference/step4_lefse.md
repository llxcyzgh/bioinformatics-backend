# LEfSe - 线性判别分析效应大小模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | lefse |
| **Description** | LEfSe（Linear Discriminant Analysis Effect Size）分析，识别组间具有统计学差异的生物标志物 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组生物标志物筛选 |
| **估算机时** | 2.0 小时 |
| **报价分数** | 3.6 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative/ | 各分类层级相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_lefse/Relative/) |
| all.mf | 样本元数据文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_lefse/all.mf) |
| lefse_vs.list | LEfSe 对比分组列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_lefse/lefse_vs.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| LEfSe.png | LDA 判别图 + 进化树合并图 | PNG | 16S/18S/ITS | 通用 | - |
| LEfSe.pdf | LDA 判别图 + 进化树合并图 | PDF | 16S/18S/ITS | 通用 | - |
| LDA.png | LDA 判别分析图 | PNG | 16S/18S/ITS | 通用 | - |
| LDA.pdf | LDA 判别分析图 | PDF | 16S/18S/ITS | 通用 | - |
| LDA.tree.png | 进化树分支图 | PNG | 16S/18S/ITS | 通用 | - |
| LDA.tree.pdf | 进化树分支图 | PDF | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_lefse.sh -i Relative/ -m all.mf -v lefse_vs.list
# 输出：LEfSe.png, LEfSe.pdf, LDA.png, LDA.pdf, LDA.tree.png, LDA.tree.pdf
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_lefse.sh -i Relative/ -m all.mf -v lefse_vs.list
# 输出：LEfSe.png, LEfSe.pdf, LDA.png, LDA.pdf, LDA.tree.png, LDA.tree.pdf
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 相对丰度表目录路径 | 是 | - | Relative/ |
| -m, --meta | 样本元数据文件路径 | 是 | - | all.mf |
| -v, --vs-list | LEfSe 对比分组列表路径 | 是 | - | lefse_vs.list |

---

## lefse_vs.list 格式

```
# LEfSe 对比分组列表
# 格式：Group1_vs_Group2
D_vs_DF
Y_vs_Z
```

**说明**：
- 每行定义一组对比（Group1_vs_Group2）
- 分组名称必须与 `all.mf` 中的分组名称一致
- 支持多组对比

---

## 流程步骤

```
1️⃣ plot_lefse.pl（执行 LEfSe 分析）
   ↓
2️⃣ 生成 LDA 判别图（LDA.png/pdf）
   ↓
3️⃣ 生成进化树分支图（LDA.tree.png/pdf）
   ↓
4️⃣ SVG → PNG/PDF 转换
   ↓
5️⃣ 合并图片（LEfSe.png/pdf）
```

---

## LEfSe 分析流程

```
1️⃣ Kruskal-Wallis 检验（组间差异）
   ↓
2️⃣ Wilcoxon 检验（组内一致性）
   ↓
3️⃣ LDA 判别分析（计算效应大小）
   ↓
4️⃣ 可视化（LDA 图 + 进化树）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **plot_lefse.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/plot_lefse.pl`
- **svg2xxx**: `/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx`
- **convert**: `/usr/bin/convert` (ImageMagick)

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export PLOT_LEFSE_PL="/your/path/to/plot_lefse.pl"' >> .env
echo 'export SVG2XXX_BIN="/your/path/to/svg2xxx"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
source .env
bash step4_lefse.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative/ | 各分类层级相对丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | LEfSe.png | 插入分析报告 |
| 报告生成 | LDA.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_lefse.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_lefse.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_lefse/`

---

最后更新：2026-04-15
