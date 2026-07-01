# 示例数据目录（`v2/examples/`）

与 [`v2/reference/README.md`](../reference/README.md) 中的 **`AMPLICON_ROOT`** 约定一致。  
本目录规范路径：**`${AMPLICON_ROOT}/v2/examples/`**；模块说明文档：**`${AMPLICON_ROOT}/v2/reference/step*.md`**。

**最后对照更新**：2026-06-24（37/37 模块已与 reference 输入表、示例目录内容对齐）

## 使用前

```bash
export AMPLICON_ROOT="/grj/BioAgent/Amplicon"   # 改为你的仓库根目录（含 v2/ 的那一层）
```

## 总览

| 项目 | 说明 |
|------|------|
| 模块数 | **37**（与 `v2/scripts/step*.sh` 一一对应） |
| 数据来源 | 测试项目 `/grj/BioAgent/test`（UOP25100039，**12 样本**，4 分组：T100/T200/T109/T209） |
| 特殊扩增 | `step4_randomforest` 为 **30 样本**（T100×15 + T200×15），满足 `MIN_SAMPLES=15` |
| 子目录 README | 每个 `step*/README.md` 含测试命令；本页汇总与 reference 的对照索引 |

## 约定

- 各目录**仅保留脚本实际需要的输入**；`group_col.list` 等多由脚本内 `color_defined.pl` 自动生成，**多数模块不提供**（少数目录保留作参考）。
- 支持双输入形态的模块（如 `-i Relative/` 或 `-i asv_table.even.txt`）在子目录 README 中均有说明。
- **`step3_dada2/manifest.tsv`** 使用绝对路径；clone 到其他机器时需更新第二列。
- 若示例与 `bash stepX_*.sh --help` 不一致，**以脚本参数为准**。

## 示例与脚本输入对照（易混模块）

| 模块 | 脚本必需输入 | 不属于本模块的示例 |
|------|-------------|-------------------|
| step5_pcoa | `-i BetaData/` 或 ordination.txt，`-g` | `*_dm.txt`（属 beta_div/catecomp） |
| step5_beta_div | `-u/-w` 距离矩阵，`-g` | ordination / PCoA 坐标 |
| step4_catecomp | `-t` even 表，`-g`；`-u/-w` dm 可选 | — |
| step5_alpha_rarefaction | `-t` even，`-g`；输出目录需预置 `alpha_index_table/` | 仅需 even 表，不需 `alpha.mf` |
| step4_otutree | `-w/-u/-r` 三文件；`-g` 可选着色 | 任意多余 `.tre` |
| step4_randomforest | `-i Relative/`，`-g`，`-r`（**每组 ≥15 样本**） | 与 simper 等 12 样本示例独立 |
| step3_upgma | `-i/-t/-m`；`-G`、PCoA 坐标可选 | `BetaData/` 软链至 `step5_pcoa/BetaData/` |

## 跨模块引用（reference 示例路径指向他处，本目录已本地化）

| 模块 | reference 指向 | 本目录实际 |
|------|----------------|------------|
| step3_alpha_data | `step3_convert_table/asv_table.even.txt` | 本地 `asv_table.even.txt` |
| step4_funpre | `step3_convert_table/featureTable.biom` | 本地 `featureTable.biom` |
| step3_upgma | `step5_pcoa/BetaData/.../ordination.txt` | 软链 `BetaData/` |

## 典型文件大小

| 类型 | 典型大小 |
|------|----------|
| 原始 fastq（单样本） | ~500K×2（gzip） |
| 拼接 fastq | ~3.3M/样本 |
| ASV 表 | asv_table.txt ~758K，even ~637K |
| 代表序列 fasta | ~2.1M |
| step3_dada2 全量 | ~352M（12 样本 manifest + fastq） |

---

## 完整模块索引（与 reference 对照）

> **文档**列链接至 `v2/reference/step*.md` 的输入/输出定义；**示例目录内容**列对应当前 `v2/examples/step*/` 实际文件。


### Step 0: 格式转换（2 个）

| 模块 | 脚本 | 示例目录内容 | 主要参数 | 文档 |
|------|------|-------------|----------|------|
| **Import_Fasta** | `step0_import_fasta.sh` | `sequences.fasta` | `-i` | [`step0_import_fasta.md`](../reference/step0_import_fasta.md) |
| **Pre_color** | `step0_pre_color.sh` | `group.list`、`group_col.list` | `-i` | [`step0_pre_color.md`](../reference/step0_pre_color.md) |

### Step 1: 数据预处理（2 个）

| 模块 | 脚本 | 示例目录内容 | 主要参数 | 文档 |
|------|------|-------------|----------|------|
| **Cutadapt** | `step1_cutadapt.sh` | `T1001.R1.fastq.gz`、`T1001.R2.fastq.gz` | `-r` `-f` | [`step1_cutadapt.md`](../reference/step1_cutadapt.md) |
| **FLASH** | `step1_flash.sh` | `T1001_R1.fastq.gz`、`T1001_R2.fastq.gz` | `-1` `-2` | [`step1_flash.md`](../reference/step1_flash.md) |

### Step 2: 质量控制（1 个）

| 模块 | 脚本 | 示例目录内容 | 主要参数 | 文档 |
|------|------|-------------|----------|------|
| **Frags_QC** | `step2_frags_qc.sh` | `T1001.extendedFrags.fastq` | `-i` | [`step2_frags_qc.md`](../reference/step2_frags_qc.md) |

### Step 3: ASV 分析（11 个）

| 模块 | 脚本 | 示例目录内容 | 主要参数 | 文档 |
|------|------|-------------|----------|------|
| **Alpha_Data** | `step3_alpha_data.sh` | `alpha.mf`、`asv_table.even.txt`、`rooted-tree.qza` | `-i` `-t` `-m` | [`step3_alpha_data.md`](../reference/step3_alpha_data.md) |
| **Beta_Data** | `step3_beta_data.sh` | `alpha.mf`、`asv_table.even.txt`、`rooted-tree.qza` | `-i` `-t` `-m` | [`step3_beta_data.md`](../reference/step3_beta_data.md) |
| **Convert_Table** | `step3_convert_table.sh` | `asv_table.even.txt`、`asv_table.txt`、`featureTable.biom` | `-i` `-t` | [`step3_convert_table.md`](../reference/step3_convert_table.md) |
| **DADA2** | `step3_dada2.sh` | `T1001.fastq`、`T1002.fastq`、`T1003.fastq`、`T1091.fastq`、`T1092.fastq`、`T1093.fastq… | `-m` `-n` | [`step3_dada2.md`](../reference/step3_dada2.md) |
| **Feature_Tables** | `step3_feature_tables.sh` | `all_tax_assignments.txt`、`asv_table.txt`、`featureTable.biom` | `-i` `-t` | [`step3_feature_tables.md`](../reference/step3_feature_tables.md) |
| **Genus_Tree** | `step3_genus_tree.sh` | `all_tax_assignments.txt`、`asv_table.g.relative.xls`、`asv_table.relative.xls`、`asv… | `-t` `-g` `-r` `-a` `-s` | [`step3_genus_tree.md`](../reference/step3_genus_tree.md) |
| **Phylogeny** | `step3_phylogeny.sh` | `featureSeqs.qza`、`rooted-tree.qza`、`rooted_tree.nwk`、`sequences.fasta`、`unrooted-… | `-i` `-n` | [`step3_phylogeny.md`](../reference/step3_phylogeny.md) |
| **Table_Stats** | `step3_table_stats.sh` | `asv_table.txt`、`group.list` | `-i` `-g` | [`step3_table_stats.md`](../reference/step3_table_stats.md) |
| **Taxonomy** | `step3_taxonomy.sh` | `feature.fasta` | `-i` `-t` `-p` | [`step3_taxonomy.md`](../reference/step3_taxonomy.md) |
| **Top_Species** | `step3_top_species.sh` | `Relative/`、`group.list` | `-i` `-g` | [`step3_top_species.md`](../reference/step3_top_species.md) |
| **UPGMA** | `step3_upgma.sh` | `BetaData/`（→ `../step5_pcoa/BetaData`）、`alpha.mf`、`asv_table.even.txt`、`asv_table… | `-i` `-t` `-m` `-G` `--unweighted-pcoa` `--weighted-pcoa` | [`step3_upgma.md`](../reference/step3_upgma.md) |

### Step 4: 可视化分析（15 个）

| 模块 | 脚本 | 示例目录内容 | 主要参数 | 文档 |
|------|------|-------------|----------|------|
| **CateComp** | `step4_catecomp.sh` | `asv_table.even.txt`、`group.list`、`unweighted_unifrac_dm.txt`、`weighted_unifrac_dm… | `-t` `-g` `-u` `-w` | [`step4_catecomp.md`](../reference/step4_catecomp.md) |
| **FunPre** | `step4_funpre.sh` | `feature.fasta`、`featureTable.biom`、`featureTable.tsv`、`group.list`、`venng.list` | `-b` `-s` `-g` `-v` | [`step4_funpre.md`](../reference/step4_funpre.md) |
| **Krona** | `step4_krona.sh` | `asv_table.even.txt` | `-t` | [`step4_krona.md`](../reference/step4_krona.md) |
| **LEfSe** | `step4_lefse.sh` | `Relative/`、`all.mf`、`asv_table.even.txt`、`group.list`、`lefse_vs.list` | `-i` `-m` `-v` | [`step4_lefse.md`](../reference/step4_lefse.md) |
| **MetaStat** | `step4_metastat.sh` | `Vs.list`、`asv_table.even.txt`、`group.list` | `-e` `-g` `-v` `-l` | [`step4_metastat.md`](../reference/step4_metastat.md) |
| **Network** | `step4_network.sh` | `genus.relative.xls`、`group.list` | `-i` `-g` | [`step4_network.md`](../reference/step4_network.md) |
| **Network3D** | `step4_network3d.sh` | `genus.relative.xls` | `-i` `-n` | [`step4_network3d.md`](../reference/step4_network3d.md) |
| **OTU_Tree** | `step4_otutree.sh` | `asv_table.even_unweighted_unifrac_upgma.tre`、`asv_table.even_weighted_unifrac_upg… | `-w` `-u` `-r` `-g` | [`step4_otutree.md`](../reference/step4_otutree.md) |
| **Random_Forest** | `step4_randomforest.sh` | `Relative/`、`group.list`、`rf.list` | `-i` `-g` `-r` `-l` | [`step4_randomforest.md`](../reference/step4_randomforest.md) |
| **Simper** | `step4_simper.sh` | `Relative/`、`asv_table.even.txt`、`group.list` | `-i` `-g` | [`step4_simper.md`](../reference/step4_simper.md) |
| **Taxa_Summary** | `step4_taxasummary.sh` | `Relative/`、`asv_table.even.txt`、`group.list` | `-i` `-g` `-l` | [`step4_taxasummary.md`](../reference/step4_taxasummary.md) |
| **Taxa_Summary_Group** | `step4_taxasummary_group.sh` | `Relative_group/`、`asv_table.even.txt`、`group.list` | `-i` `-g` `-l` | [`step4_taxasummary_group.md`](../reference/step4_taxasummary_group.md) |
| **Ternary** | `step4_ternary.sh` | `Relative_group/`、`ternary.list` | `-i` `-l` | [`step4_ternary.md`](../reference/step4_ternary.md) |
| **T_test** | `step4_ttest.sh` | `Relative/`、`group.list` | `-i` `-g` `--method` | [`step4_ttest.md`](../reference/step4_ttest.md) |
| **Venn** | `step4_venn.sh` | `asv_table.even.txt`、`asv_table.group.even.txt`、`group.list`、`venn.G.list` | `-t` `-l` `-g` | [`step4_venn.md`](../reference/step4_venn.md) |

### Step 5: 多样性分析（6 个）

| 模块 | 脚本 | 示例目录内容 | 主要参数 | 文档 |
|------|------|-------------|----------|------|
| **Alpha_Div** | `step5_alpha_div.sh` | `alpha_diversity_index.txt`、`group.list`、`group_col.list` | `-i` `-g` | [`step5_alpha_div.md`](../reference/step5_alpha_div.md) |
| **Alpha_Rarefaction** | `step5_alpha_rarefaction.sh` | `alpha_index_table/`、`asv_table.even.txt`、`group.list` | `-p` `-r` `-t` `-g` | [`step5_alpha_rarefaction.md`](../reference/step5_alpha_rarefaction.md) |
| **Beta_Div** | `step5_beta_div.sh` | `group.list`、`unweighted_unifrac_dm.txt`、`weighted_unifrac_dm.txt` | `-u` `-w` `-g` | [`step5_beta_div.md`](../reference/step5_beta_div.md) |
| **NMDS** | `step5_nmds.sh` | `Relative/`、`asv_table.even.txt`、`group.list` | `-i` `-g` `-l` | [`step5_nmds.md`](../reference/step5_nmds.md) |
| **PCA** | `step5_pca.sh` | `Relative/`、`asv_table.even.txt`、`group.list` | `-i` `-g` `-l` | [`step5_pca.md`](../reference/step5_pca.md) |
| **PCoA** | `step5_pcoa.sh` | `BetaData/`、`group.list` | `-i` `-g` `-d` | [`step5_pcoa.md`](../reference/step5_pcoa.md) |

---

## 子目录 README

每个 `step*/README.md` 提供：

1. 输入文件清单（与 reference **输入**表一致）
2. 可直接复制的测试命令（`${AMPLICON_ROOT}/v2/scripts/...`）

快速进入某一模块：

```bash
cat "${AMPLICON_ROOT}/v2/examples/step5_pcoa/README.md"
bash "${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh" --help
less "${AMPLICON_ROOT}/v2/reference/step5_pcoa.md"
```
