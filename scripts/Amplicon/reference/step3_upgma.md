# UPGMA - 基于 UniFrac 距离的系统发育树模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | upgma |
| **Description** | 基于 Unweighted/Weighted UniFrac 距离矩阵构建 UPGMA 系统发育树，展示样本间的系统发育关系 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Beta 多样性分析 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化 ASV 表（样本） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_upgma/asv_table.even.txt) |
| rooted-tree.nwk | 有根系统发育树 | NWK | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_upgma/rooted-tree.nwk) |
| alpha.mf | 样本元数据（表头：`#SampleID	Description`） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_upgma/alpha.mf) |
| asv_table.group.even.txt | 分组均一化表（可选） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_upgma/asv_table.group.even.txt) |
| ordination.txt | PCoA 坐标源文件（可选，来自 step3_beta_data 导出） | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_upgma/BetaData/weighted_unifrac_pcoa_results_qza/ordination.txt) |

---

## 输出

> 输入为 `asv_table.even.txt` 时，BIOM 基名为 `asv_table.even`；提供 `-G asv_table.group.even.txt` 时，分组 BIOM 基名为 `asv_table.group.even`。以下路径中的 `{basename}` 对应该基名。

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| UPGMA_sample/unrarefied_bdiv/{basename}_unweighted_unifrac_upgma.tre | 样本 Unweighted UPGMA 树（Newick） | TRE | 16S/18S/ITS | 通用 | - |
| UPGMA_sample/unrarefied_bdiv/{basename}_weighted_unifrac_upgma.tre | 样本 Weighted UPGMA 树（Newick） | TRE | 16S/18S/ITS | 通用 | - |
| UPGMA_sample/unweighted_unifrac/unweighted_unifrac.pdf | 样本 Unweighted 树（带 bootstrap） | PDF | 16S/18S/ITS | 通用 | - |
| UPGMA_sample/unweighted_unifrac/unweighted_unifrac.png | 样本 Unweighted 树 | PNG | 16S/18S/ITS | 通用 | - |
| UPGMA_sample/weighted_unifrac/weighted_unifrac.pdf | 样本 Weighted 树（带 bootstrap） | PDF | 16S/18S/ITS | 通用 | - |
| UPGMA_sample/weighted_unifrac/weighted_unifrac.png | 样本 Weighted 树 | PNG | 16S/18S/ITS | 通用 | - |
| UPGMA_group/unrarefied_bdiv/{basename}_unweighted_unifrac_upgma.tre | 分组 Unweighted UPGMA 树（可选） | TRE | 16S/18S/ITS | 通用 | - |
| UPGMA_group/unrarefied_bdiv/{basename}_weighted_unifrac_upgma.tre | 分组 Weighted UPGMA 树（可选） | TRE | 16S/18S/ITS | 通用 | - |
| UPGMA_group/unweighted_unifrac/unweighted_unifrac.png | 分组 Unweighted 树（可选） | PNG | 16S/18S/ITS | 通用 | - |
| UPGMA_group/weighted_unifrac/weighted_unifrac.png | 分组 Weighted 树（可选） | PNG | 16S/18S/ITS | 通用 | - |
| PCoA_data/unweighted_unifrac_dm.txt | 样本非加权距离矩阵 | TXT | 16S/18S/ITS | 通用 | - |
| PCoA_data/weighted_unifrac_dm.txt | 样本加权距离矩阵 | TXT | 16S/18S/ITS | 通用 | - |
| PCoA_data/unweighted_unifrac_group_dm.txt | 分组非加权距离矩阵（可选） | TXT | 16S/18S/ITS | 通用 | - |
| PCoA_data/weighted_unifrac_group_dm.txt | 分组加权距离矩阵（可选） | TXT | 16S/18S/ITS | 通用 | - |
| PCoA_data/unweighted_unifrac_pc.txt | 非加权 PCoA 坐标（可选） | TXT | 16S/18S/ITS | 通用 | - |
| PCoA_data/weighted_unifrac_pc.txt | 加权 PCoA 坐标（可选） | TXT | 16S/18S/ITS | 通用 | - |

**常见样本 `.tre` 路径示例**（`-i asv_table.even.txt`）：
- `UPGMA_sample/unrarefied_bdiv/asv_table.even_unweighted_unifrac_upgma.tre`
- `UPGMA_sample/unrarefied_bdiv/asv_table.even_weighted_unifrac_upgma.tre`

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_upgma.sh \
    -i asv_table.even.txt \
    -t rooted-tree.nwk \
    -m alpha.mf \
    -o UPGMA_Output/
```

**示例 1**：样本 UPGMA 树
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_upgma.sh \
    -i asv_table.even.txt \
    -t rooted-tree.nwk \
    -m alpha.mf \
    -o UPGMA_Output/
```

**示例 2**：样本 + 分组 UPGMA（group.mf 由 alpha.mf 自动生成）
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_upgma.sh \
    -i asv_table.even.txt \
    -t rooted-tree.nwk \
    -m alpha.mf \
    -G asv_table.group.even.txt \
    --unweighted-pcoa BetaData_Output/unweighted_unifrac_pcoa_results_qza/ordination.txt \
    --weighted-pcoa BetaData_Output/weighted_unifrac_pcoa_results_qza/ordination.txt \
    -o UPGMA_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 均一化 ASV 表（TSV/TXT 或 BIOM） | 是 | - | asv_table.even.txt |
| -t, --tree | 有根系统发育树路径 | 是 | - | rooted-tree.nwk |
| -m, --meta | 样本元数据（需含 `#SampleID	Description` 表头，缺失时自动补全） | 是 | - | alpha.mf |
| -G, --group-input | 分组均一化表（group.mf 由 -m 自动生成） | 否 | - | asv_table.group.even.txt |
| --unweighted-pcoa | 非加权 UniFrac ordination.txt（来自 step3_beta_data） | 否 | - | ordination.txt |
| --weighted-pcoa | 加权 UniFrac ordination.txt（来自 step3_beta_data） | 否 | - | ordination.txt |
| -d, --depth-table | 计算 seqs_per_sample 用的 TSV（输入为 BIOM 时） | 否 | 同 -i（若为 TSV） | asv_table.even.txt |
| -o, --output | 输出目录 | 是 | - | UPGMA_Output/ |

### 元数据格式

**alpha.mf**（样本元数据，同时用于生成分组 group.mf）：
```
#SampleID	Description
D1	D
D2	D
Y.K1	Y
...
```

**自动生成的 group.mf**（提供 `-G` 时，从 alpha.mf 的 Description 列提取唯一组名）：
```
#SampleID	Description
D	D
Y	Y
...
```

---

## 流程步骤

```
1️⃣ 元数据表头校验 / 补全
   ↓
2️⃣ TSV → BIOM（biom convert）
   ↓
3️⃣ 自动计算 seqs_per_sample（均一化表首列样本 reads 总和）
   ↓
4️⃣ jackknifed_beta_diversity.py（样本 UPGMA）
   ↓
5️⃣ make_bootstrapped_tree.py + convert（unweighted / weighted 树图）
   ↓
6️⃣ 距离矩阵整理到 PCoA_data/
   ↓
7️⃣ pcoa.pl 导出 PCoA 坐标（可选，需 step3_beta_data 的 ordination.txt）
   ↓
8️⃣ 分组 UPGMA（提供 -G 时，由 alpha.mf 生成 group.mf 并重复 4–6）
```

---

## UPGMA 树类型

| 树类型 | 距离算法 | 是否考虑丰度 | 说明 |
|--------|---------|-------------|------|
| **Unweighted UniFrac** | 非加权 | ❌ 否 | 基于进化关系的定性距离 |
| **Weighted UniFrac** | 加权 | ✅ 是 | 基于进化关系的定量距离 |

---

## 环境配置

### 默认路径

- **QIIME2 conda**: `CONDA_BIN` + `CONDA_ENV`（默认 16s-env，用于 biom convert）
- **QIIME1**: `QIIME1_CONDA_BIN` + `QIIME1_ENV`（默认 qiime1）
- **pcoa.pl**: `.../03.ASV/betaAnalysis/pcoa.pl`
- **convert**: `/usr/bin/convert`

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SEQS_PER_SAMPLE | 手动指定采样深度 | 从均一化表自动计算 |

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt, asv_table.group.even.txt | 均一化表 |
| step3_phylogeny | rooted-tree.nwk | 有根系统发育树 |
| step3_beta_data | ordination.txt | PCoA 坐标（可选） |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step4_otutree | `-w`/`-u`：`UPGMA_sample/unrarefied_bdiv/*_upgma.tre`；`-r`：`top10/asv_table.p10.relative.xls` | 样本 OTU 树可视化 |
| step4_otutree | `-w`/`-u`：`UPGMA_group/unrarefied_bdiv/*_upgma.tre`；`-r`：`top10_group/asv_table.p10.group.relative.xls` | 分组 OTU 树可视化（需 `-G`） |
| step5_pcoa | BetaData/*_pcoa_results_qza/ordination.txt 或 PCoA_data/*_pc.txt | PCoA 排序图（推荐 `-i BetaData/ -d`；旧流程可用 pc 文件） |
| step4_catecomp | PCoA_data/*_dm.txt | 分类比较统计 |
| 报告生成 | UPGMA_sample/*.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step3_upgma.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step3_upgma.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step3_upgma/`
- **参考流程**: `Step8.UPGMA.sh`

---

最后更新：2026-06-24
