# 扩增子分析智能体 - 模块文档库

本目录包含扩增子测序分析流程中各个工具的详细文档，用于构建扩增子分析智能体。

**版本**: v2.0  
**最后更新**: 2026-04-15  
**模块总数**: 35 个

---

## 根路径变量 `AMPLICON_ROOT`

全仓库的 **reference 文档** 与 **scripts 调用示例** 中，凡出现脚本路径、同仓库文档路径、示例根目录，一律用环境变量 **`AMPLICON_ROOT`** 表示 **本 openclaw 仓库根目录**（包含 `scripts/`、`reference/`、`examples/` 的那一层）。

```bash
# 使用前在 shell 或规划器生成的脚本开头设置（路径改为你的 clone 位置）
export AMPLICON_ROOT="/vol1/guorongjun/BioAgent/Amplicon/openclaw"
```

| 路径类型 | 写法 |
|----------|------|
| 可执行脚本 | `${AMPLICON_ROOT}/scripts/step*.sh` |
| 本目录下的模块说明 | `${AMPLICON_ROOT}/reference/step*.md` |
| 示例数据目录 | `${AMPLICON_ROOT}/examples/step*/` |

各子文档中的 `` `bash ${AMPLICON_ROOT}/scripts/...` `` 等均依赖 **`AMPLICON_ROOT` 已导出**。规划器生成最终命令时，应保证在调用前注入该变量（或展开为实际绝对路径）。

---

## 📊 模块库统计

| 步骤 | 模块数 | 状态 | 说明 |
|------|--------|------|------|
| **Step 0** | 2 | ✅ 完成 | 格式转换 |
| **Step 1** | 2 | ✅ 完成 | 数据预处理 |
| **Step 2** | 1 | ✅ 完成 | 质量控制 |
| **Step 3** | 10 | ✅ 完成 | ASV 分析 |
| **Step 4** | 15 | ✅ 完成 | 可视化分析 |
| **Step 5** | 6 | ✅ 完成 | 多样性分析 |
| **总计** | **36** | **✅ 完成** | 完整流程 |

---

## 📁 完整模块列表

### Step 0: 格式转换（1 个）

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

### Step 3: ASV 分析（10 个）

| 模块 | 脚本 | 功能 |
|------|------|------|
| **DADA2** | `step3_dada2.sh` | ASV 推断与降噪 |
| **Taxonomy** | `step3_taxonomy.sh` | VSEARCH 物种注释 |
| **Phylogeny** | `step3_phylogeny.sh` | 系统发育树构建 |
| **Feature_Tables** | `step3_feature_tables.sh` | ASV 特征表构建 |
| **Table_Stats** | `step3_table_stats.sh` | ASV 表统计分析 |
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
| **PCA_PCoA** | `step5_pca_pcoa.sh` | PCA/PCoA 排序 |
| **NMDS** | `step5_nmds.sh` | NMDS 分析 |
| **DCA** | `step5_dca.sh` | DCA 分析 |

---

## 🚀 快速开始

### 场景 1: 只有 FASTA 序列，做物种注释

```bash
export AMPLICON_ROOT="/vol1/guorongjun/BioAgent/Amplicon/openclaw"   # 按实际部署修改

# Step 0: FASTA → QIIME2
bash "${AMPLICON_ROOT}/scripts/step0_import_fasta.sh" \
    -i sequences.fasta \
    -o Import_Output/

# Step 3: 物种注释
bash "${AMPLICON_ROOT}/scripts/step3_taxonomy.sh" \
    -i Import_Output/featureSeqs.qza \
    -o Taxonomy_Output/ \
    -t 16S \
    -p 16
```

### 场景 2: 完整扩增子分析流程

```bash
export AMPLICON_ROOT="/vol1/guorongjun/BioAgent/Amplicon/openclaw"   # 按实际部署修改

# Step 1: 数据预处理
bash "${AMPLICON_ROOT}/scripts/step1_cutadapt.sh" -i input.fastq.gz -o Cutadapt_Output/ -f F_PRIMER -r R_PRIMER
bash "${AMPLICON_ROOT}/scripts/step1_flash.sh" -1 R1.fastq.gz -2 R2.fastq.gz -o Flash_Output/

# Step 2: 质量控制
bash "${AMPLICON_ROOT}/scripts/step2_frags_qc.sh" -i input.fastq -o Frags_QC_Output/

# Step 3: ASV 分析
bash "${AMPLICON_ROOT}/scripts/step3_dada2.sh" -m manifest.tsv -o DADA2_Output/
bash "${AMPLICON_ROOT}/scripts/step3_taxonomy.sh" -i DADA2_Output/featureSeqs.qza -o Taxonomy_Output/ -t 16S

# Step 4: 可视化分析
bash "${AMPLICON_ROOT}/scripts/step4_venn.sh" -t asv_table.group.even.txt -l venn.G.list -o Venn_Output/
bash "${AMPLICON_ROOT}/scripts/step4_lefse.sh" -i Relative/ -m all.mf -v lefse_vs.list -o LEfSe_Output/

# Step 5: 多样性分析
bash "${AMPLICON_ROOT}/scripts/step5_alpha_div.sh" -i alpha_diversity_index.txt -g group_col.list -o Alpha_Div_Output/
bash "${AMPLICON_ROOT}/scripts/step5_beta_div.sh" -wu unweighted.dm -w weighted.dm -o Beta_Div_Output/
```

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
ls "${AMPLICON_ROOT}/reference/step"*.md

# 查看特定模块
cat "${AMPLICON_ROOT}/reference/step3_taxonomy.md"

# 查看脚本帮助
bash "${AMPLICON_ROOT}/scripts/step3_taxonomy.sh" --help
```

### 智能体调用

所有脚本都采用统一的接口：

```bash
bash "${AMPLICON_ROOT}/scripts/stepX_module.sh" \
    -i input_file \
    -o output_dir \
    [其他参数]
```

---

## 📂 目录结构（`${AMPLICON_ROOT}` 下）

```
${AMPLICON_ROOT}/
├── scripts/                      # 可执行脚本
│   ├── step0_import_fasta.sh
│   ├── step1_cutadapt.sh
│   ├── step1_flash.sh
│   ├── step2_frags_qc.sh
│   ├── step3_*.sh
│   ├── step4_*.sh
│   └── step5_*.sh
│
├── reference/                    # 模块文档（本目录）
│   ├── README.md                 # 本文档
│   └── step*.md
│
└── examples/                     # 各 step 示例数据与 README
    └── step*/
```

---

## 🔗 相关资源

- **脚本目录**: `${AMPLICON_ROOT}/scripts/`
- **示例数据**: `${AMPLICON_ROOT}/examples/`（按 step 子目录浏览；总说明见该目录下 `README.md`）

---

## 📞 联系与维护

- **维护者**: 允思拓生物信息团队
- **公司**: 允思拓（天津）生物科技有限公司
- **仓库根路径**: 由部署方设置 `AMPLICON_ROOT`（见上文）
- **文档版本**: v2.0
- **最后更新**: 2026-04-15

---

*扩增子分析智能体 - 让微生物组分析更智能、更高效* 🌿
