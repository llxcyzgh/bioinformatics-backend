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
| asv_table.even.txt | 均一化 ASV 表（step3 输出，传入时脚本自动生成 Relative/） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_lefse/asv_table.even.txt) |
| Relative/ | 各分类层级相对丰度表目录（也可直接传入） | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_lefse/Relative/) |
| all.mf | 样本元数据文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_lefse/all.mf) |
| lefse_vs.list | LEfSe 对比分组列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_lefse/lefse_vs.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative/ | 脚本内生成的各层级相对丰度表（-i 为 even 表时） | DIR | 16S/18S/ITS | 通用 | - |
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
bash ${AMPLICON_ROOT}/v2/scripts/step4_lefse.sh \
    -i TableStats/asv_table.even.txt \
    -m all.mf \
    -v lefse_vs.list \
    -o LEfSe_Output/
```

**示例**（直接传入 Relative/）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_lefse.sh \
    -i Relative/ \
    -m all.mf \
    -v lefse_vs.list \
    -o LEfSe_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | Relative/ 目录或 asv_table.even.txt | 是 | - | TableStats/asv_table.even.txt |
| -m, --meta | 样本元数据文件路径 | 是 | - | all.mf |
| -v, --vs-list | LEfSe 对比分组列表路径 | 是 | - | lefse_vs.list |
| -o, --output | 输出目录 | 是 | - | LEfSe_Output/ |

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
0️⃣ stat_otu_tab.pl：asv_table.even.txt → Relative/（-i 为 even 表时）
   ↓
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
- **stat_otu_tab.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl`
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
bash step4_lefse.sh ... -o LEfSe_Output/
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
| 报告生成 | LEfSe.png | 插入分析报告 |
| 报告生成 | LDA.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step4_lefse.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step4_lefse.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step4_lefse/`

---

最后更新：2026-06-26
