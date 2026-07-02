"""
脚本调用注册表：每个 tool_id 映射到其脚本路径、文件参数和输出文件定义。
用于编排脚本生成器生成正确的 bash 调用命令。

数据来源：scripts/Amplicon/reference/*.md
"""

from pydantic import BaseModel


class ParamDef(BaseModel):
    flag: str
    data_type: str  # ToolDef data type 或特殊类型（_PRIMER_F, _MANIFEST, _METADATA, _GROUP_LIST）
    required: bool = True
    default: str | None = None
    description: str | None = None  # 来自 .md 参数说明列，仅供展示


class OutputFileDef(BaseModel):
    data_type: str
    filename: str  # 具体文件名或模式（${sample} 可用）


class ScriptCallDef(BaseModel):
    tool_id: str
    script_path: str
    params: list[ParamDef]
    outputs: list[OutputFileDef]
    per_sample: bool = False


TOOL_SCRIPT_CALLS: dict[str, ScriptCallDef] = {
    # ─── 数据预处理 ───
    "amp-import-fasta": ScriptCallDef(
        tool_id="amp-import-fasta",
        script_path="Amplicon/scripts/step0_import_fasta.sh",
        params=[
            ParamDef(flag="-i", data_type="FASTA_SEQ"),
            ParamDef(flag="-o", data_type="_OUTPUT_DIR", default="Import_Output"),
            ParamDef(flag="-t", data_type="_QIIME_TYPE", default="FeatureData[Sequence]", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="FEATURE_SEQS", filename="featureSeqs.qza"),
        ],
    ),
    "amp-pre-color": ScriptCallDef(
        tool_id="amp-pre-color",
        script_path="Amplicon/scripts/step0_pre_color.sh",
        params=[
            ParamDef(flag="-i", data_type="_GROUP_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="GROUP_COLOR_LIST", filename="group_col.list"),
        ],
    ),
    "amp-cutadapt": ScriptCallDef(
        tool_id="amp-cutadapt",
        script_path="Amplicon/scripts/step1_cutadapt.sh",
        params=[
            ParamDef(flag="-r1", data_type="FASTQ_R1"),
            ParamDef(flag="-r2", data_type="FASTQ_R2"),
            ParamDef(flag="-f", data_type="_PRIMER_F"),
            ParamDef(flag="-r", data_type="_PRIMER_R"),
            ParamDef(flag="-e", data_type="_CONFIG", default="0.1", required=False),
            ParamDef(flag="-l", data_type="_CONFIG", default="100", required=False),
            ParamDef(flag="-n", data_type="_CONFIG", default="1", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="TRIMMED_R1", filename="${sample}.cutadapt.R1.fastq.gz"),
            OutputFileDef(data_type="TRIMMED_R2", filename="${sample}.cutadapt.R2.fastq.gz"),
        ],
        per_sample=True,
    ),
    "amp-flash": ScriptCallDef(
        tool_id="amp-flash",
        script_path="Amplicon/scripts/step1_flash.sh",
        params=[
            ParamDef(flag="-1", data_type="TRIMMED_R1"),
            ParamDef(flag="-2", data_type="TRIMMED_R2"),
            ParamDef(flag="-m", data_type="_CONFIG", default="10", required=False),
            ParamDef(flag="-M", data_type="_CONFIG", default="250", required=False),
            ParamDef(flag="-x", data_type="_CONFIG", default="0.1", required=False),
            ParamDef(flag="-t", data_type="_CONFIG", default="1", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="FASTQ_MERGED", filename="${sample}.extendedFrags.fastq"),
        ],
        per_sample=True,
    ),
    # ─── 质量控制 ───
    "amp-frags-qc": ScriptCallDef(
        tool_id="amp-frags-qc",
        script_path="Amplicon/scripts/step2_frags_qc.sh",
        params=[
            ParamDef(flag="-i", data_type="FASTQ_MERGED"),
            ParamDef(flag="-q", data_type="_CONFIG", default="19", required=False),
            ParamDef(flag="-u", data_type="_CONFIG", default="15", required=False),
            ParamDef(flag="-d", data_type="_CONFIG", default="", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="FASTQ_QC", filename="${sample}.fastq"),
        ],
        per_sample=True,
    ),
    # ─── 核心分析 ───
    "amp-dada2": ScriptCallDef(
        tool_id="amp-dada2",
        script_path="Amplicon/scripts/step3_dada2.sh",
        params=[
            ParamDef(flag="-m", data_type="_MANIFEST"),
            ParamDef(flag="-t", data_type="_CONFIG", default="0", required=False),
            ParamDef(flag="-n", data_type="_CONFIG", default="12", required=False),
            ParamDef(flag="-a", data_type="_CONFIG", default="1", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="FEATURE_SEQS", filename="featureSeqs.qza"),
            OutputFileDef(data_type="FEATURE_TABLE", filename="featureTable.biom"),
            OutputFileDef(data_type="FEATURE_FASTA", filename="feature.fasta"),
        ],
    ),
    "amp-taxonomy": ScriptCallDef(
        tool_id="amp-taxonomy",
        script_path="Amplicon/scripts/step3_taxonomy.sh",
        params=[
            ParamDef(flag="-i", data_type="FEATURE_SEQS"),
            ParamDef(flag="-t", data_type="_AMPLICON_TYPE", default="16S"),
            ParamDef(flag="-p", data_type="_CONFIG", default="16", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="TAXONOMY_ASSIGN", filename="all_tax_assignments.txt"),
        ],
    ),
    "amp-phylogeny": ScriptCallDef(
        tool_id="amp-phylogeny",
        script_path="Amplicon/scripts/step3_phylogeny.sh",
        params=[
            ParamDef(flag="-i", data_type="FEATURE_SEQS"),
            ParamDef(flag="-n", data_type="_CONFIG", default="12", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="ROOTED_TREE", filename="rooted-tree.qza"),
            OutputFileDef(data_type="TREE_NWK", filename="rooted_tree.nwk"),
        ],
    ),
    "amp-feature-tables": ScriptCallDef(
        tool_id="amp-feature-tables",
        script_path="Amplicon/scripts/step3_feature_tables.sh",
        params=[
            ParamDef(flag="-i", data_type="FEATURE_TABLE"),
            ParamDef(flag="-t", data_type="TAXONOMY_ASSIGN"),
        ],
        outputs=[
            OutputFileDef(data_type="ASV_TABLE", filename="asv_table.txt"),
        ],
    ),
    "amp-table-stats": ScriptCallDef(
        tool_id="amp-table-stats",
        script_path="Amplicon/scripts/step3_table_stats.sh",
        params=[
            ParamDef(flag="-i", data_type="ASV_TABLE"),
        ],
        outputs=[
            OutputFileDef(data_type="ASV_TABLE_EVEN", filename="asv_table.even.txt"),
            OutputFileDef(data_type="RELATIVE_ABUNDANCE", filename="Relative/"),
            OutputFileDef(data_type="GROUP_EVEN_TABLE", filename="asv_table.group.even.txt"),
            OutputFileDef(data_type="GROUP_REL_ABUNDANCE", filename="Relative_group/"),
            OutputFileDef(data_type="EVEN_ABS_ABUNDANCE", filename="evenabs/"),
        ],
    ),
    "amp-convert-table": ScriptCallDef(
        tool_id="amp-convert-table",
        script_path="Amplicon/scripts/step3_convert_table.sh",
        params=[
            ParamDef(flag="-i", data_type="FEATURE_TABLE"),
            ParamDef(flag="-t", data_type="_CONFIG", default="FeatureTable[Frequency]", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="FEATURE_TABLE_QZA", filename="{basename}.qza"),
        ],
    ),
    # ─── 多样性分析 ───
    "amp-alpha-data": ScriptCallDef(
        tool_id="amp-alpha-data",
        script_path="Amplicon/scripts/step3_alpha_data.sh",
        params=[
            ParamDef(flag="-i", data_type="ASV_TABLE_EVEN"),
            ParamDef(flag="-t", data_type="ROOTED_TREE", required=False),
            ParamDef(flag="-m", data_type="_METADATA", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="ALPHA_INDEX", filename="alpha_index_table/alpha_diversity_index.txt"),
        ],
    ),
    "amp-beta-data": ScriptCallDef(
        tool_id="amp-beta-data",
        script_path="Amplicon/scripts/step3_beta_data.sh",
        params=[
            ParamDef(flag="-i", data_type="ASV_TABLE_EVEN"),
            ParamDef(flag="-t", data_type="ROOTED_TREE"),
            ParamDef(flag="-m", data_type="_METADATA"),
        ],
        outputs=[
            OutputFileDef(data_type="DIST_MATRIX", filename="bray_curtis_distance_matrix.qza"),
            # PCOA_COORDS 用空串代表整个 BetaData_Output 目录（pcoa -i 目录模式消费它）；
            # 真正的坐标在每个 *_pcoa_results_qza/ordination.txt 里，由 beta-data 解压 .qza 产出。
            OutputFileDef(data_type="PCOA_COORDS", filename=""),
        ],
    ),
    "amp-upgma": ScriptCallDef(
        tool_id="amp-upgma",
        script_path="Amplicon/scripts/step3_upgma.sh",
        params=[
            ParamDef(flag="-i", data_type="ASV_TABLE_EVEN"),
            ParamDef(flag="-t", data_type="TREE_NWK"),
            ParamDef(flag="-m", data_type="_METADATA"),
        ],
        outputs=[
            OutputFileDef(data_type="UPGMA_TREE", filename="UPGMA_sample/"),
            OutputFileDef(data_type="DIST_MATRIX", filename="PCoA_data/"),
            OutputFileDef(data_type="PCOA_COORDS", filename="PCoA_data/"),
        ],
    ),
    "amp-alpha-div": ScriptCallDef(
        tool_id="amp-alpha-div",
        script_path="Amplicon/scripts/step5_alpha_div.sh",
        params=[
            ParamDef(flag="-i", data_type="ALPHA_INDEX"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="ALPHA_SIG", filename="anova_test.txt"),
        ],
    ),
    "amp-alpha-rarefaction": ScriptCallDef(
        tool_id="amp-alpha-rarefaction",
        script_path="Amplicon/scripts/step5_alpha_rarefaction.sh",
        params=[
            ParamDef(flag="-t", data_type="ASV_TABLE_EVEN"),
            ParamDef(flag="-m", data_type="_METADATA"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="RAREFACTION_CURVE", filename="rank_abundance.png"),
        ],
    ),
    "amp-beta-div": ScriptCallDef(
        tool_id="amp-beta-div",
        script_path="Amplicon/scripts/step5_beta_div.sh",
        params=[
            ParamDef(flag="-u", data_type="DIST_MATRIX"),
            ParamDef(flag="-w", data_type="DIST_MATRIX"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="BETA_SIG", filename="beta_diff.png"),
        ],
    ),
    # ─── 统计检验 ───
    "amp-catecomp": ScriptCallDef(
        tool_id="amp-catecomp",
        script_path="Amplicon/scripts/step4_catecomp.sh",
        params=[
            ParamDef(flag="-t", data_type="ASV_TABLE_EVEN"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
            ParamDef(flag="-u", data_type="DIST_MATRIX", required=False),
            ParamDef(flag="-w", data_type="DIST_MATRIX", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="CATECOMP_RESULT", filename="Anosim/"),
        ],
    ),
    "amp-lefse": ScriptCallDef(
        tool_id="amp-lefse",
        script_path="Amplicon/scripts/step4_lefse.sh",
        params=[
            ParamDef(flag="-i", data_type="RELATIVE_ABUNDANCE"),
            ParamDef(flag="-m", data_type="_METADATA"),
            ParamDef(flag="-v", data_type="_VS_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="LEFSE_RESULT", filename="LEfSe.png"),
        ],
    ),
    "amp-metastat": ScriptCallDef(
        tool_id="amp-metastat",
        script_path="Amplicon/scripts/step4_metastat.sh",
        params=[
            ParamDef(flag="-e", data_type="EVEN_ABS_ABUNDANCE"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
            ParamDef(flag="-v", data_type="_VS_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="METASTAT_RESULT", filename="phylum/"),
        ],
    ),
    "amp-randomforest": ScriptCallDef(
        tool_id="amp-randomforest",
        script_path="Amplicon/scripts/step4_randomforest.sh",
        params=[
            ParamDef(flag="-i", data_type="RELATIVE_ABUNDANCE"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
            ParamDef(flag="-r", data_type="_RF_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="RF_RESULT", filename="auc.png"),
        ],
    ),
    "amp-simper": ScriptCallDef(
        tool_id="amp-simper",
        script_path="Amplicon/scripts/step4_simper.sh",
        params=[
            ParamDef(flag="-i", data_type="RELATIVE_ABUNDANCE"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
            ParamDef(flag="--top", data_type="_CONFIG", default="10", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="SIMPER_RESULT", filename="simper_result/"),
        ],
    ),
    "amp-ttest": ScriptCallDef(
        tool_id="amp-ttest",
        script_path="Amplicon/scripts/step4_ttest.sh",
        params=[
            ParamDef(flag="-i", data_type="RELATIVE_ABUNDANCE"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
            ParamDef(flag="--threshold", data_type="_CONFIG", default="0.05", required=False),
            ParamDef(flag="--method", data_type="_CONFIG", default="t", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="TTEST_RESULT", filename="ttest_result/"),
        ],
    ),
    # ─── 可视化 ───
    "amp-top-species": ScriptCallDef(
        tool_id="amp-top-species",
        script_path="Amplicon/scripts/step3_top_species.sh",
        params=[
            ParamDef(flag="-i", data_type="RELATIVE_ABUNDANCE"),
        ],
        outputs=[
            OutputFileDef(data_type="TOP_SPECIES", filename="top10/"),
        ],
    ),
    "amp-genus-tree": ScriptCallDef(
        tool_id="amp-genus-tree",
        script_path="Amplicon/scripts/step3_genus_tree.sh",
        params=[
            ParamDef(flag="-t", data_type="TAXONOMY_ASSIGN"),
            ParamDef(flag="-g", data_type="GROUP_REL_ABUNDANCE"),
            ParamDef(flag="-s", data_type="FEATURE_FASTA"),
        ],
        outputs=[
            OutputFileDef(data_type="GENUS_TREE", filename="genus_evolutionary_tree/"),
        ],
    ),
    "amp-krona": ScriptCallDef(
        tool_id="amp-krona",
        script_path="Amplicon/scripts/step4_krona.sh",
        params=[
            ParamDef(flag="-t", data_type="ASV_TABLE_EVEN"),
            ParamDef(flag="-o", data_type="_CONFIG", default="krona", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="KRONA_CHART", filename="krona.html"),
        ],
    ),
    "amp-network": ScriptCallDef(
        tool_id="amp-network",
        script_path="Amplicon/scripts/step4_network.sh",
        params=[
            ParamDef(flag="-i", data_type="RELATIVE_ABUNDANCE"),
            ParamDef(flag="-y", data_type="_GROUP_Y_LIST"),
            ParamDef(flag="-z", data_type="_GROUP_Z_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="NETWORK_2D", filename="Y/dot/network.js"),
        ],
    ),
    "amp-network3d": ScriptCallDef(
        tool_id="amp-network3d",
        script_path="Amplicon/scripts/step4_network3d.sh",
        params=[
            ParamDef(flag="-i", data_type="RELATIVE_ABUNDANCE"),
            ParamDef(flag="-n", data_type="_CONFIG", default="100", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="NETWORK_3D", filename="network3D.html"),
        ],
    ),
    "amp-otutree": ScriptCallDef(
        tool_id="amp-otutree",
        script_path="Amplicon/scripts/step4_otutree.sh",
        params=[
            ParamDef(flag="-t", data_type="UPGMA_TREE"),
            ParamDef(flag="-r", data_type="RELATIVE_ABUNDANCE"),
        ],
        outputs=[
            OutputFileDef(data_type="OTU_TREE", filename="UPGMA.W.tree.png"),
        ],
    ),
    "amp-taxasummary": ScriptCallDef(
        tool_id="amp-taxasummary",
        script_path="Amplicon/scripts/step4_taxasummary.sh",
        params=[
            ParamDef(flag="-i", data_type="RELATIVE_ABUNDANCE"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
            ParamDef(flag="--top", data_type="_CONFIG", default="35", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="TAXA_HEATMAP", filename="cluster/"),
        ],
    ),
    "amp-taxasummary-group": ScriptCallDef(
        tool_id="amp-taxasummary-group",
        script_path="Amplicon/scripts/step4_taxasummary_group.sh",
        params=[
            ParamDef(flag="-i", data_type="GROUP_REL_ABUNDANCE"),
            ParamDef(flag="--top", data_type="_CONFIG", default="35", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="TAXA_GROUP_HEATMAP", filename="cluster/"),
        ],
    ),
    "amp-ternary": ScriptCallDef(
        tool_id="amp-ternary",
        script_path="Amplicon/scripts/step4_ternary.sh",
        params=[
            ParamDef(flag="-i", data_type="GROUP_REL_ABUNDANCE"),
            ParamDef(flag="-l", data_type="_TERNARY_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="TERNARY_CHART", filename="ternary.png"),
        ],
    ),
    "amp-venn": ScriptCallDef(
        tool_id="amp-venn",
        script_path="Amplicon/scripts/step4_venn.sh",
        params=[
            ParamDef(flag="-t", data_type="GROUP_EVEN_TABLE"),
            ParamDef(flag="-l", data_type="_VENN_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="VENN_CHART", filename="Venn_group/"),
        ],
    ),
    # ─── 排序分析 ───
    "amp-pca": ScriptCallDef(
        tool_id="amp-pca",
        script_path="Amplicon/scripts/step5_pca.sh",
        params=[
            ParamDef(flag="-r", data_type="RELATIVE_ABUNDANCE"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="PCA_PLOT", filename="UOA_pca.png"),
        ],
    ),
    "amp-pcoa": ScriptCallDef(
        tool_id="amp-pcoa",
        script_path="Amplicon/scripts/step5_pcoa.sh",
        params=[
            # -i 目录模式：吃 beta-data/upgma 的输出目录（内含 *_pcoa_results_qza/ordination.txt）。
            # 旧的 -w/-wu 期望 weighted/unweighted unifrac 的 .txt，且 PCOA_COORDS 会被解析成单个
            # .qza，类型/语义都错；改用脚本首选的 -i <BetaData_Output/> 目录模式。
            ParamDef(flag="-i", data_type="PCOA_COORDS"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="PCOA_PLOT", filename="PCoA.png"),
        ],
    ),
    "amp-nmds": ScriptCallDef(
        tool_id="amp-nmds",
        script_path="Amplicon/scripts/step5_nmds.sh",
        params=[
            ParamDef(flag="-t", data_type="ASV_TABLE_EVEN"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
            ParamDef(flag="-c", data_type="_CONFIG", default="", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="NMDS_PLOT", filename="NMDS.png"),
        ],
    ),
    # ─── 功能预测 ───
    "amp-funpre": ScriptCallDef(
        tool_id="amp-funpre",
        script_path="Amplicon/scripts/step4_funpre.sh",
        params=[
            ParamDef(flag="-b", data_type="FEATURE_TABLE"),
            ParamDef(flag="-s", data_type="FEATURE_FASTA"),
            ParamDef(flag="-g", data_type="_GROUP_LIST", required=False),
            ParamDef(flag="-v", data_type="_CONFIG", default="", required=False),
        ],
        outputs=[
            OutputFileDef(data_type="FUNC_PREDICTION", filename="EC_metagenome_out/"),
        ],
    ),
}

# ─── v2 契约：每个脚本都强制 `-o <输出目录>` ──────────────────────────
# v1 只有 import-fasta 真正实现 -o；v2 给所有脚本补齐（产物写进 -o 指定的目录，
# 路径从脚本外部可知）。这里在模块加载时统一给每个 ScriptCallDef 注入一个
# `-o _OUTPUT_DIR` ParamDef（默认值取 v2 文档的 <Tool>_Output 命名），于是：
#   • 算法编排器遇到 _OUTPUT_DIR 会发 `-o ${<TOOL>_OUT}`，并把产物注册成
#     `${<TOOL>_OUT}/<file>`，使下一步 -i 准确指向上一步的输出目录；
#   • backfill_domains 会把它照常序列化进 DB 的 scripts.call_params，LLM 紧凑契约
#     也能读到。
# 注入到运行时对象上，规范化掉工具自带的旧 -o（如 krona 旧的 -o _CONFIG）。
OUTPUT_DIR_DEFAULTS: dict[str, str] = {
    "amp-import-fasta": "Import_Output",
    "amp-pre-color": "Color_Output",
    "amp-cutadapt": "Cutadapt_Output",
    "amp-flash": "Flash_Output",
    "amp-frags-qc": "Frags_QC_Output",
    "amp-dada2": "DADA2_Output",
    "amp-convert-table": "ConvertTable_Output",
    "amp-taxonomy": "Taxonomy_Output",
    "amp-phylogeny": "Phylogeny_Output",
    "amp-feature-tables": "FeatureTables_Output",
    "amp-table-stats": "TableStats_Output",
    "amp-alpha-data": "AlphaData_Output",
    "amp-beta-data": "BetaData_Output",
    "amp-upgma": "UPGMA_Output",
    "amp-top-species": "TopSpecies_Output",
    "amp-genus-tree": "GenusTree_Output",
    "amp-catecomp": "CateComp_Output",
    "amp-lefse": "LEfSe_Output",
    "amp-metastat": "MetaStat_Output",
    "amp-randomforest": "RandomForest_Output",
    "amp-simper": "Simper_Output",
    "amp-ttest": "Ttest_Output",
    "amp-krona": "Krona_Output",
    "amp-network": "Network_Output",
    "amp-network3d": "Network3D_Output",
    "amp-otutree": "OTUTree_Output",
    "amp-taxasummary": "TaxaSummary_Output",
    "amp-taxasummary-group": "TaxaSummaryGroup_Output",
    "amp-ternary": "Ternary_Output",
    "amp-venn": "Venn_Output",
    "amp-alpha-div": "AlphaDiv_Output",
    "amp-alpha-rarefaction": "AlphaRarefaction_Output",
    "amp-beta-div": "BetaDiv_Output",
    "amp-pca": "PCA_Output",
    "amp-pcoa": "PCoA_Output",
    "amp-nmds": "NMDS_Output",
    "amp-funpre": "FunPre_Output",
}

for _tid, _cd in list(TOOL_SCRIPT_CALLS.items()):
    _cd.params = [p for p in _cd.params if p.flag != "-o"] + [
        ParamDef(
            flag="-o",
            data_type="_OUTPUT_DIR",
            default=OUTPUT_DIR_DEFAULTS.get(_tid, _tid[4:].title().replace("-", "_") + "_Output"),
            required=True,
        )
    ]
del _tid, _cd

# 常用引物预设
COMMON_PRIMERS = {
    "16S V3-V4": {"f": "ACTCCTACGGGAGGCAGCAG", "r": "GGACTACHVGGGTWTCTAAT"},
    "16S V4": {"f": "GTGCCAGCMGCCGCGGTAA", "r": "GGACTACHVGGGTWTCTAAT"},
    "ITS1": {"f": "CTTGGTCATTTAGAGGAAGTAA", "r": "GCTGCGTTCTTCATCGATGC"},
    "ITS2": {"f": "GCATCGATGAAGAACGCAGC", "r": "TCCTCCGCTTATTGATATGC"},
}


def get_script_call(tool_id: str) -> ScriptCallDef | None:
    return TOOL_SCRIPT_CALLS.get(tool_id)
