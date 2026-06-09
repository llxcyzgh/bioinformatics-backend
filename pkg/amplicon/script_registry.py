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
            OutputFileDef(data_type="FASTQ_MERGED", filename="${sample}.out.extendedFrags.fastq"),
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
            OutputFileDef(data_type="PCOA_COORDS", filename="bray_curtis_pcoa_results.qza"),
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
            ParamDef(flag="-w", data_type="PCOA_COORDS"),
            ParamDef(flag="-wu", data_type="PCOA_COORDS"),
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
    "amp-dca": ScriptCallDef(
        tool_id="amp-dca",
        script_path="Amplicon/scripts/step5_dca.sh",
        params=[
            ParamDef(flag="-t", data_type="ASV_TABLE_EVEN"),
            ParamDef(flag="-g", data_type="_GROUP_LIST"),
        ],
        outputs=[
            OutputFileDef(data_type="DCA_PLOT", filename="DCA.png"),
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

# 常用引物预设
COMMON_PRIMERS = {
    "16S V3-V4": {"f": "ACTCCTACGGGAGGCAGCAG", "r": "GGACTACHVGGGTWTCTAAT"},
    "16S V4": {"f": "GTGCCAGCMGCCGCGGTAA", "r": "GGACTACHVGGGTWTCTAAT"},
    "ITS1": {"f": "CTTGGTCATTTAGAGGAAGTAA", "r": "GCTGCGTTCTTCATCGATGC"},
    "ITS2": {"f": "GCATCGATGAAGAACGCAGC", "r": "TCCTCCGCTTATTGATATGC"},
}


def get_script_call(tool_id: str) -> ScriptCallDef | None:
    return TOOL_SCRIPT_CALLS.get(tool_id)
