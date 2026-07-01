# 扩增子分析智能体 - 模块文档库

本目录包含扩增子测序分析流程中各个工具的详细文档，用于构建扩增子分析智能体。

**版本**: v2.1（显式 -o 输出目录）  
**最后更新**: 2026-06-24  
**模块总数**: 37 个

---

## 根路径变量 `AMPLICON_ROOT`

全仓库的 **reference 文档** 与 **scripts 调用示例** 中，凡出现脚本路径、同仓库文档路径、示例根目录，一律用环境变量 **`AMPLICON_ROOT`** 表示 **本 openclaw 仓库根目录**（包含 `v2/scripts/`、`v2/reference/`、`examples/` 的那一层）。

```bash
# 使用前在 shell 或规划器生成的脚本开头设置（路径改为你的 clone 位置）
export AMPLICON_ROOT="/vol1/guorongjun/BioAgent/Amplicon/openclaw"
```

| 路径类型 | 写法 |
|----------|------|
| 可执行脚本 | `${AMPLICON_ROOT}/v2/scripts/step*.sh` |
| 本目录下的模块说明 | `${AMPLICON_ROOT}/v2/reference/step*.md` |
| 示例数据目录 | `${AMPLICON_ROOT}/v2/examples/step*/` |

各子文档中的 `` `bash ${AMPLICON_ROOT}/v2/scripts/...` `` 等均依赖 **`AMPLICON_ROOT` 已导出**。规划器生成最终命令时，应保证在调用前注入该变量（或展开为实际绝对路径）。

---

## 📊 模块库统计

| 步骤 | 模块数 | 状态 | 说明 |
|------|--------|------|------|
| **Step 0** | 2 | ✅ 完成 | 格式转换 |
| **Step 1** | 2 | ✅ 完成 | 数据预处理 |
| **Step 2** | 1 | ✅ 完成 | 质量控制 |
| **Step 3** | 11 | ✅ 完成 | ASV 分析 |
| **Step 4** | 15 | ✅ 完成 | 可视化分析 |
| **Step 5** | 6 | ✅ 完成 | 多样性分析 |
| **总计** | **37** | **✅ 完成** | 完整流程 |

---

## 📁 完整模块列表

### Step 0: 格式转换（2 个）

| 模块 | 脚本 | 功能 |
|------|------|------|
| **Import_Fasta** | `step0_import_fasta.sh` | FASTA → QIIME2 格式转换 |
| **Pre_color** | `step0_pre_color.sh` | 分组颜色配置文件生成 |

### Step 1: 数据预处理（2 个）

| 模块 | 脚本 | 功能 |
|------|------|------|
| **Cutadapt** | `step1_cutadapt.sh` | 引物序列修剪 |
| **FLASH** | `step1_flash.sh` | 双端序列拼接 |

### Step 2: 质量控制（1 个）

| 模块 | 脚本 | 功能 |
|------|------|------|
| **Frags_QC** | `step2_frags_qc.sh` | 序列质量控制 |

### Step 3: ASV 分析（11 个）

| 模块 | 脚本 | 功能 |
|------|------|------|
| **DADA2** | `step3_dada2.sh` | ASV 推断与降噪 |
| **Taxonomy** | `step3_taxonomy.sh` | VSEARCH 物种注释 |
| **Phylogeny** | `step3_phylogeny.sh` | 系统发育树构建 |
| **Feature_Tables** | `step3_feature_tables.sh` | ASV 特征表构建 |
| **Table_Stats** | `step3_table_stats.sh` | ASV 表统计分析 |
| **Top_Species** | `step3_top_species.sh` | Top10 物种与柱状图 |
| **Alpha_Data** | `step3_alpha_data.sh` | Alpha 多样性分析 |
| **Beta_Data** | `step3_beta_data.sh` | Beta 多样性分析 |
| **UPGMA** | `step3_upgma.sh` | UPGMA 树构建 |
| **Genus_Tree** | `step3_genus_tree.sh` | 属水平进化树 |
| **Convert_Table** | `step3_convert_table.sh` | TSV/BIOM → QIIME2 转换 |

### Step 4: 可视化分析（15 个）

| 模块 | 脚本 | 功能 |
|------|------|------|
| **Venn** | `step4_venn.sh` | 维恩图分析 |
| **T_test** | `step4_ttest.sh` | T 检验/Wilcoxon 分析 |
| **LEfSe** | `step4_lefse.sh` | LEfSe 生物标志物 |
| **MetaStat** | `step4_metastat.sh` | MetaStat 差异分析 |
| **Random_Forest** | `step4_randomforest.sh` | 随机森林分析 |
| **Krona** | `step4_krona.sh` | Krona 交互式图 |
| **Ternary** | `step4_ternary.sh` | 三元相图 |
| **Simper** | `step4_simper.sh` | SIMPER 分析 |
| **OTU_Tree** | `step4_otutree.sh` | OTU 树关联分析 |
| **Taxa_Summary** | `step4_taxasummary.sh` | 物种热图（样本） |
| **Taxa_Summary_Group** | `step4_taxasummary_group.sh` | 物种热图（分组） |
| **CateComp** | `step4_catecomp.sh` | 分类比较统计 |
| **Network** | `step4_network.sh` | 2D 物种网络 |
| **Network3D** | `step4_network3d.sh` | 3D 物种网络 |
| **FunPre** | `step4_funpre.sh` | PICRUSt2 功能预测 |

### Step 5: 多样性分析（6 个）

| 模块 | 脚本 | 功能 |
|------|------|------|
| **Alpha_Rarefaction** | `step5_alpha_rarefaction.sh` | Alpha 稀化曲线 |
| **Alpha_Div** | `step5_alpha_div.sh` | Alpha 多样性差异 |
| **Beta_Div** | `step5_beta_div.sh` | Beta 多样性差异 |
| **PCA** | `step5_pca.sh` | PCA 主成分分析 |
| **PCoA** | `step5_pcoa.sh` | PCoA 主坐标分析 |
| **NMDS** | `step5_nmds.sh` | NMDS 分析 |

---

## 🚀 快速开始

### 场景 1: 只有 FASTA 序列，做物种注释

```bash
export AMPLICON_ROOT="/vol1/guorongjun/BioAgent/Amplicon/openclaw"   # 按实际部署修改

# Step 0: FASTA → QIIME2
bash "${AMPLICON_ROOT}/v2/scripts/step0_import_fasta.sh" \
    -i sequences.fasta \
    -o Import_Output/

# Step 3: 物种注释
bash "${AMPLICON_ROOT}/v2/scripts/step3_taxonomy.sh" \
    -i Import_Output/featureSeqs.qza \
    -o Taxonomy_Output/ \
    -t 16S \
    -p 16
```

### 场景 2: 完整扩增子分析流程

从原始测序数据到物种组成、差异分析、排序分析与多样性统计的**全模块串联示例**。  
下列命令假设项目目录 `${PROJECT}` 下已准备：

| 配置文件 | 说明 |
|----------|------|
| `group.list` | 样本分组（Tab：样本ID、组名） |
| `alpha.mf` | 样本元数据（表头 `#SampleID\tDescription`，与 QIIME2 兼容） |
| `manifest.tsv` | DADA2 样本 manifest（质控后生成） |
| `venn.G.list` / `lefse_vs.list` / `rf.list` / `ternary.list` | 各模块对比/分组列表（按需） |

```bash
export AMPLICON_ROOT="/vol1/guorongjun/BioAgent/Amplicon/openclaw"   # 按实际部署修改
export PROJECT="/path/to/your_project"                               # 项目根目录
export GROUP="${PROJECT}/group.list"
export ALPHA_MF="${PROJECT}/alpha.mf"

# =============================================================================
# Step 1: 数据预处理（双端测序；每个样本需分别运行 cutadapt，再 flash 拼接）
# =============================================================================
bash "${AMPLICON_ROOT}/v2/scripts/step1_cutadapt.sh" \
    -r1 "${PROJECT}/raw/Sample.R1.fastq.gz" \
    -r2 "${PROJECT}/raw/Sample.R2.fastq.gz" \
    -f GTGCCAGCMGCCGCGGTAA -r GGACTACHVGGGTWTCTAAT \
    -o "${PROJECT}/01_Cutadapt/Sample/"

bash "${AMPLICON_ROOT}/v2/scripts/step1_flash.sh" \
    -1 "${PROJECT}/01_Cutadapt/Sample/Sample.R1.fastq.gz" \
    -2 "${PROJECT}/01_Cutadapt/Sample/Sample.R2.fastq.gz" \
    -o "${PROJECT}/02_Flash/Sample/"

# =============================================================================
# Step 2: 质量控制
# =============================================================================
bash "${AMPLICON_ROOT}/v2/scripts/step2_frags_qc.sh" \
    -i "${PROJECT}/02_Flash/Sample/Sample.extendedFrags.fastq" \
    -o "${PROJECT}/03_FragsQC/Sample/"

# 所有样本质控完成后，编写 manifest.tsv 指向 03_FragsQC/*/Sample.fastq

# =============================================================================
# Step 3: ASV 推断、注释、特征表与均一化（核心数据层）
# =============================================================================
bash "${AMPLICON_ROOT}/v2/scripts/step3_dada2.sh" \
    -m "${PROJECT}/manifest.tsv" -t 0 -n 12 \
    -o "${PROJECT}/04_DADA2/"

bash "${AMPLICON_ROOT}/v2/scripts/step3_taxonomy.sh" \
    -i "${PROJECT}/04_DADA2/featureSeqs.qza" -t 16S -p 16 \
    -o "${PROJECT}/05_Taxonomy/"

bash "${AMPLICON_ROOT}/v2/scripts/step3_phylogeny.sh" \
    -i "${PROJECT}/04_DADA2/featureSeqs.qza" -n 12 \
    -o "${PROJECT}/06_Phylogeny/"

bash "${AMPLICON_ROOT}/v2/scripts/step3_feature_tables.sh" \
    -i "${PROJECT}/04_DADA2/featureTable.biom" \
    -t "${PROJECT}/05_Taxonomy/all_tax_assignments.txt" \
    -o "${PROJECT}/07_FeatureTables/"

bash "${AMPLICON_ROOT}/v2/scripts/step3_table_stats.sh" \
    -i "${PROJECT}/07_FeatureTables/asv_table.txt" \
    -g "${GROUP}" \
    -o "${PROJECT}/08_TableStats/"
# 产出：asv_table.even.txt, Relative/, Relative_group/, asv_table.group.even.txt

bash "${AMPLICON_ROOT}/v2/scripts/step3_alpha_data.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -t "${PROJECT}/06_Phylogeny/rooted-tree.qza" \
    -m "${ALPHA_MF}" \
    -o "${PROJECT}/09_AlphaData/"

bash "${AMPLICON_ROOT}/v2/scripts/step3_beta_data.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -t "${PROJECT}/06_Phylogeny/rooted-tree.qza" \
    -m "${ALPHA_MF}" \
    -o "${PROJECT}/10_BetaData/"

bash "${AMPLICON_ROOT}/v2/scripts/step3_upgma.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -t "${PROJECT}/06_Phylogeny/rooted_tree.nwk" \
    -m "${ALPHA_MF}" \
    -G "${PROJECT}/08_TableStats/asv_table.group.even.txt" \
    --unweighted-pcoa "${PROJECT}/10_BetaData/unweighted_unifrac_pcoa_results_qza/ordination.txt" \
    --weighted-pcoa "${PROJECT}/10_BetaData/weighted_unifrac_pcoa_results_qza/ordination.txt" \
    -o "${PROJECT}/11_UPGMA/"

bash "${AMPLICON_ROOT}/v2/scripts/step3_top_species.sh" \
    -i "${PROJECT}/08_TableStats/Relative/" \
    -g "${GROUP}" \
    -o "${PROJECT}/12_TopSpecies/"

bash "${AMPLICON_ROOT}/v2/scripts/step3_genus_tree.sh" \
    -t "${PROJECT}/05_Taxonomy/all_tax_assignments.txt" \
    -g "${PROJECT}/08_TableStats/Relative/asv_table.g.relative.xls" \
    -r "${PROJECT}/08_TableStats/Relative/asv_table.relative.xls" \
    -a "${PROJECT}/07_FeatureTables/asv_table.txt" \
    -s "${PROJECT}/04_DADA2/feature.fasta" \
    -G "${PROJECT}/08_TableStats/Relative_group/asv_table_group.g.relative.xls" \
    -o "${PROJECT}/13_GenusTree/"

# =============================================================================
# Step 4: 物种组成与群落结构可视化（15 个模块）
# =============================================================================
bash "${AMPLICON_ROOT}/v2/scripts/step4_krona.sh" \
    -t "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -o "${PROJECT}/14_Krona/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_taxasummary.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -o "${PROJECT}/15_TaxaSummary/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -o "${PROJECT}/16_TaxaSummaryGroup/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_venn.sh" \
    -t "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -l "${PROJECT}/venn.G.list" \
    -o "${PROJECT}/17_Venn/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_ternary.sh" \
    -i "${PROJECT}/08_TableStats/Relative_group/" \
    -l "${PROJECT}/ternary.list" \
    -o "${PROJECT}/18_Ternary/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_otutree.sh" \
    -w "${PROJECT}/11_UPGMA/UPGMA_sample/unrarefied_bdiv/asv_table.even_weighted_unifrac_upgma.tre" \
    -u "${PROJECT}/11_UPGMA/UPGMA_sample/unrarefied_bdiv/asv_table.even_unweighted_unifrac_upgma.tre" \
    -r "${PROJECT}/12_TopSpecies/top10/asv_table.p10.relative.xls" \
    -g "${GROUP}" \
    -o "${PROJECT}/19_OTUTree_sample/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_otutree.sh" \
    -w "${PROJECT}/11_UPGMA/UPGMA_group/unrarefied_bdiv/asv_table.group.even_weighted_unifrac_upgma.tre" \
    -u "${PROJECT}/11_UPGMA/UPGMA_group/unrarefied_bdiv/asv_table.group.even_unweighted_unifrac_upgma.tre" \
    -r "${PROJECT}/12_TopSpecies/top10_group/asv_table.p10.group.relative.xls" \
    -g "${GROUP}" \
    -o "${PROJECT}/20_OTUTree_group/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_network.sh" \
    -i "${PROJECT}/08_TableStats/Relative/asv_table.g.relative.xls" \
    -g "${GROUP}" \
    -o "${PROJECT}/21_Network/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_network3d.sh" \
    -i "${PROJECT}/08_TableStats/Relative/asv_table.g.relative.xls" \
    -o "${PROJECT}/22_Network3D/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_ttest.sh" \
    -i "${PROJECT}/08_TableStats/Relative/" \
    -g "${GROUP}" \
    -o "${PROJECT}/23_Ttest/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_metastat.sh" \
    -e "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -v "${PROJECT}/Vs.list" \
    -o "${PROJECT}/24_MetaStat/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_simper.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -o "${PROJECT}/25_Simper/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_lefse.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -m "${PROJECT}/all.mf" \
    -v "${PROJECT}/lefse_vs.list" \
    -o "${PROJECT}/26_LEfSe/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_randomforest.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -r "${PROJECT}/rf.list" \
    -o "${PROJECT}/27_RandomForest/"

bash "${AMPLICON_ROOT}/v2/scripts/step4_catecomp.sh" \
    -t "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -u "${PROJECT}/11_UPGMA/PCoA_data/unweighted_unifrac_dm.txt" \
    -w "${PROJECT}/11_UPGMA/PCoA_data/weighted_unifrac_dm.txt" \
    -o "${PROJECT}/28_CateComp/"

# PICRUSt2 功能预测（16S 细菌/古菌；ITS/18S 通常跳过）
bash "${AMPLICON_ROOT}/v2/scripts/step4_funpre.sh" \
    -b "${PROJECT}/04_DADA2/featureTable.biom" \
    -s "${PROJECT}/04_DADA2/feature.fasta" \
    -g "${GROUP}" \
    -v "${PROJECT}/venng.list" \
    -o "${PROJECT}/29_FunPre/"

# =============================================================================
# Step 5: Alpha / Beta 多样性深度分析（6 个模块）
# =============================================================================
# alpha_rarefaction 依赖 step3_alpha_data 的 alpha_index_table（需复制到输出目录）
mkdir -p "${PROJECT}/30_AlphaRarefaction"
cp -r "${PROJECT}/09_AlphaData/alpha_index_table" "${PROJECT}/30_AlphaRarefaction/"
bash "${AMPLICON_ROOT}/v2/scripts/step5_alpha_rarefaction.sh" \
    -t "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -o "${PROJECT}/30_AlphaRarefaction/"

bash "${AMPLICON_ROOT}/v2/scripts/step5_alpha_div.sh" \
    -i "${PROJECT}/09_AlphaData/alpha_index_table/alpha_diversity_index.txt" \
    -g "${GROUP}" \
    -o "${PROJECT}/31_AlphaDiv/"

bash "${AMPLICON_ROOT}/v2/scripts/step5_beta_div.sh" \
    -u "${PROJECT}/11_UPGMA/PCoA_data/unweighted_unifrac_dm.txt" \
    -w "${PROJECT}/11_UPGMA/PCoA_data/weighted_unifrac_dm.txt" \
    -g "${GROUP}" \
    -o "${PROJECT}/32_BetaDiv/"

bash "${AMPLICON_ROOT}/v2/scripts/step5_pca.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -o "${PROJECT}/33_PCA/"

bash "${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh" \
    -i "${PROJECT}/10_BetaData/" \
    -d weighted_unifrac,unweighted_unifrac,jaccard,bray_curtis \
    -g "${GROUP}" \
    -o "${PROJECT}/34_PCoA/"

bash "${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh" \
    -i "${PROJECT}/08_TableStats/asv_table.even.txt" \
    -g "${GROUP}" \
    -l genus \
    -o "${PROJECT}/35_NMDS/"
```

**流程说明**：

| 阶段 | 模块数 | 关键产出 |
|------|--------|----------|
| Step 1–2 | 3 | 质控后 fastq、manifest |
| Step 3 | 11 | `asv_table.even.txt`、`Relative/`、`BetaData/`、UPGMA 树 |
| Step 4 | 15 | 热图、维恩图、差异分析、网络、LEfSe、Random Forest 等 |
| Step 5 | 6 | 稀化曲线、Alpha/Beta 差异、PCA/PCoA/NMDS |

**可选模块**：
- `step0_import_fasta.sh`：已有 FASTA、无原始测序时使用（见场景 1）
- `step0_pre_color.sh`：单独预生成颜色配置（多数 Step 4/5 脚本会自动调用 `color_defined.pl`）
- `step3_convert_table.sh`：额外 QIIME2 格式转换（`step3_beta_data` 内部也会按需转换）
- `step4_funpre.sh`：仅适用于 16S 细菌/古菌功能预测

**并行提示**：Step 4 各模块彼此独立，在 `08_TableStats/` 与 `10_BetaData/` 就绪后可并行提交。

---

## 📋 文档结构

每个模块文档包含以下部分：

1. **基本信息** - 工具名称、描述、适用范围
2. **输入** - 输入文件列表（名称、格式、说明）
3. **输出** - 输出文件列表（名称、格式、说明）
4. **执行命令** - 调用脚本的命令示例
5. **参数说明** - 参数列表（说明、必需性、默认值）
6. **相关文件** - 脚本位置和参考文档

---

## 🛠️ 使用方式

### 命令行调用

```bash
export AMPLICON_ROOT="/vol1/guorongjun/BioAgent/Amplicon/openclaw"   # 按实际部署修改

# 查看所有模块
ls "${AMPLICON_ROOT}/v2/reference/step"*.md

# 查看特定模块
cat "${AMPLICON_ROOT}/v2/reference/step3_taxonomy.md"

# 查看脚本帮助
bash "${AMPLICON_ROOT}/v2/scripts/step3_taxonomy.sh" --help
```

### 智能体调用

**统一约定**：全部 37 个脚本均要求 **`-o output_dir`**（输出目录）。  
**主输入参数不统一**——不能默认所有模块都用 `-i`；规划命令时应查阅对应 `step*.md` 或运行 `--help`。

**通用调用形式**：

```bash
bash "${AMPLICON_ROOT}/v2/scripts/stepX_module.sh" \
    <主输入参数> \
    -o output_dir \
    [其他参数]
```

**主输入参数分类**：

| 类型 | 参数 | 适用脚本 |
|------|------|----------|
| 单文件 `-i` | `-i <path>` | step0_import_fasta、step0_pre_color、step2_frags_qc、step3_table_stats、step3_taxonomy、step3_phylogeny、step3_top_species、step3_alpha_data、step3_convert_table、step4_taxasummary、step4_taxasummary_group、step4_ttest、step4_lefse、step4_simper、step4_randomforest、step4_network、step4_network3d、step4_ternary、step5_alpha_div、step5_pca、step5_nmds、step5_pcoa（`-i BetaData/` 或 ordination.txt） |
| 表文件 `-t` | `-t <table>` | step4_krona、step4_venn、step4_catecomp、step5_alpha_rarefaction |
| 均一化表 `-e` | `-e <even.txt>` | step4_metastat |
| Manifest `-m` | `-m <manifest.tsv>` | step3_dada2 |
| 双端测序 | `-r1/-r2/-f/-r` 或 `-1/-2` | step1_cutadapt、step1_flash |
| 多文件组合 | 见下表 | step3_genus_tree、step3_feature_tables、step3_beta_data、step3_upgma、step4_funpre、step4_otutree、step5_beta_div |

**各脚本主输入与常见附加必需参数**：

| 脚本 | 主输入 | 常见附加必需参数 |
|------|--------|------------------|
| step0_import_fasta | `-i` fasta | — |
| step0_pre_color | `-i` group | — |
| step1_cutadapt | `-r1` `-r2` `-f` `-r` | — |
| step1_flash | `-1` `-2` | — |
| step2_frags_qc | `-i` fastq | — |
| step3_dada2 | `-m` manifest | — |
| step3_taxonomy | `-i` qza/fasta | `-t` 16S/18S/ITS |
| step3_phylogeny | `-i` qza/fasta | — |
| step3_feature_tables | `-i` biom | `-t` 注释表 |
| step3_table_stats | `-i` asv_table | `-g`（需分组统计时） |
| step3_convert_table | `-i` 表 | `-t` 类型 |
| step3_alpha_data | `-i` even 表 | `-t` 树、`-m` 元数据（稀化曲线时） |
| step3_beta_data | `-i` even 表 | `-t` 树、`-m` 元数据 |
| step3_upgma | `-i` even 表 | `-t` 树、`-m` 元数据 |
| step3_top_species | `-i` Relative/ | `-g`（分组 Top10 时） |
| step3_genus_tree | `-t` `-g` `-r` `-a` `-s` | `-G`（分组树，可选） |
| step4_krona | `-t` even 表 | — |
| step4_venn | `-t` even/group 表 | `-l` venn 列表；`-g`（even 表时） |
| step4_metastat | `-e` even 表 | `-g` `-v` Vs.list |
| step4_catecomp | `-t` even 表 | `-g` |
| step4_funpre | `-b` biom `-s` fasta | `-g` `-v`（可选） |
| step4_otutree | `-w` `-u` `-r` | `-g`（可选） |
| step5_alpha_rarefaction | `-t` even 表 | `-g` |
| step5_beta_div | `-u` `-w` 距离矩阵 | `-g` |
| step5_pcoa | `-i` BetaData/ **或** `-w`/`-wu` pc 文件 | `-g` |

> **注意**：`-t` 在不同脚本中含义不同——在 step4_krona/venn/catecomp、step5_alpha_rarefaction 中表示 **table（特征表）**；在 step3_taxonomy 中表示 **标记类型（16S/18S/ITS）**；在 step3_feature_tables 中表示 **taxonomy 注释文件**。

**智能体规划建议**：

1. 先读 `${AMPLICON_ROOT}/v2/reference/stepX_*.md` 获取完整参数表与上下游依赖  
2. 生成命令时 **必含 `-o`**，主输入按上表映射，勿硬编码 `-i`  
3. 多输入模块（如 genus_tree、otutree、funpre）在元数据中显式列出全部必填参数  
4. 不确定时执行 `bash .../stepX_*.sh --help` 核对

---

## 📂 目录结构（`${AMPLICON_ROOT}` 下）

```
${AMPLICON_ROOT}/
├── v2/
│   ├── scripts/                      # 可执行脚本
│   │   ├── step0_*.sh
│   │   ├── step1_*.sh
│   │   ├── step2_*.sh
│   │   ├── step3_*.sh
│   │   ├── step4_*.sh
│   │   └── step5_*.sh
│   │
│   └── reference/                    # 模块文档（本目录）
│       ├── README.md                 # 本文档
│       └── step*.md
│
└── examples/                         # 各 step 示例数据与 README
    └── step*/
```

---

## 🔗 相关资源

- **脚本目录**: `${AMPLICON_ROOT}/v2/scripts/`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/`（按 step 子目录浏览；总说明见该目录下 `README.md`）

---

## 📞 联系与维护

- **维护者**: 允思拓生物信息团队
- **公司**: 允思拓（天津）生物科技有限公司
- **仓库根路径**: 由部署方设置 `AMPLICON_ROOT`（见上文）
- **文档版本**: v2.1
- **最后更新**: 2026-06-30

---

*扩增子分析智能体 - 让微生物组分析更智能、更高效* 🌿
