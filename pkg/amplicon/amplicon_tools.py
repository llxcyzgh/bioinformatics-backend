"""
Amplicon 分析流水线工具定义

每个工具抽象为 输入数据类型集合 → 输出数据类型集合
数据流关系基于各脚本 MD 文档的实际描述
"""

from pydantic import BaseModel


class ToolDef(BaseModel):
    id: str
    name: str
    inputs: list[str]
    outputs: list[str]
    category: str


# ─── 数据类型 ID → 中文显示名 ──────────────────────────

DATA_TYPE_NAMES: dict[str, str] = {
    "FASTA_SEQ": "FASTA序列文件",
    "FASTQ_PAIR": "双端测序原始数据",
    "FASTQ_TRIMMED": "引物切除后序列",
    "FASTQ_MERGED": "FLASH拼接序列",
    "FASTQ_QC": "质控后序列",
    "FEATURE_SEQS": "ASV代表序列(QZA)",
    "FEATURE_TABLE": "ASV丰度表(BIOM)",
    "FEATURE_FASTA": "ASV序列(FASTA)",
    "TAXONOMY_ASSIGN": "物种分类注释结果",
    "ASV_TABLE": "ASV特征表(含分类)",
    "ASV_TABLE_EVEN": "均一化ASV表",
    "RELATIVE_ABUNDANCE": "相对丰度表",
    "ROOTED_TREE": "有根系统发育树(QZA)",
    "TREE_NWK": "Newick格式树文件",
    "ALPHA_INDEX": "Alpha多样性指数",
    "DIST_MATRIX": "Beta距离矩阵",
    "PCOA_COORDS": "PCoA坐标",
    "UPGMA_TREE": "UPGMA聚类树",
    "GROUP_EVEN_TABLE": "组水平均一化表",
    "GROUP_REL_ABUNDANCE": "组水平相对丰度",
    "EVEN_ABS_ABUNDANCE": "均一化绝对丰度",
    "ALPHA_SIG": "Alpha多样性检验结果",
    "RAREFACTION_CURVE": "稀疏曲线",
    "BETA_SIG": "Beta多样性检验结果",
    "CATECOMP_RESULT": "群落差异检验结果",
    "LEFSE_RESULT": "LEfSe差异分析结果",
    "METASTAT_RESULT": "MetaStat差异分析结果",
    "RF_RESULT": "随机森林分类结果",
    "SIMPER_RESULT": "SIMPER分析结果",
    "TTEST_RESULT": "T检验/Wilcoxon结果",
    "TOP_SPECIES": "Top10物种柱状图",
    "GENUS_TREE": "属水平系统发育树",
    "KRONA_CHART": "Krona分类组成图",
    "NETWORK_2D": "2D共发生网络图",
    "NETWORK_3D": "3D网络图",
    "OTU_TREE": "OTU系统发育树热图",
    "TAXA_HEATMAP": "物种组成热图",
    "TAXA_GROUP_HEATMAP": "分组物种热图",
    "TERNARY_CHART": "三元相图",
    "VENN_CHART": "Venn图",
    "PCA_PLOT": "PCA排序图",
    "PCOA_PLOT": "PCoA排序图",
    "NMDS_PLOT": "NMDS排序图",
    "DCA_PLOT": "DCA排序图",
    "FUNC_PREDICTION": "功能预测结果",
}


def _t(
    id: str, name: str, inputs: list[str], outputs: list[str], category: str
) -> ToolDef:
    return ToolDef(id=f"amp-{id}", name=name, inputs=inputs, outputs=outputs, category=category)


def get_all_tools() -> list[ToolDef]:
    return [
        # 数据预处理
        _t("import-fasta", "FASTA导入QIIME2", ["FASTA_SEQ"], ["FEATURE_SEQS"], "数据预处理"),
        _t("cutadapt", "Cutadapt引物切除", ["FASTQ_PAIR"], ["FASTQ_TRIMMED"], "数据预处理"),
        _t("flash", "FLASH双端拼接", ["FASTQ_TRIMMED"], ["FASTQ_MERGED"], "数据预处理"),
        # 质量控制
        _t("frags-qc", "序列质量控制", ["FASTQ_MERGED"], ["FASTQ_QC"], "质量控制"),
        # 核心分析
        _t("dada2", "DADA2 ASV推断与去噪", ["FASTQ_QC"], ["FEATURE_SEQS", "FEATURE_TABLE", "FEATURE_FASTA"], "核心分析"),
        _t("taxonomy", "物种分类注释", ["FEATURE_SEQS"], ["TAXONOMY_ASSIGN"], "核心分析"),
        _t("phylogeny", "系统发育树构建", ["FEATURE_SEQS"], ["ROOTED_TREE", "TREE_NWK"], "核心分析"),
        _t("feature-tables", "ASV特征表构建", ["FEATURE_TABLE", "TAXONOMY_ASSIGN"], ["ASV_TABLE"], "核心分析"),
        _t("table-stats", "ASV表均一化与丰度计算", ["ASV_TABLE"], ["ASV_TABLE_EVEN", "RELATIVE_ABUNDANCE", "GROUP_EVEN_TABLE", "GROUP_REL_ABUNDANCE", "EVEN_ABS_ABUNDANCE"], "核心分析"),
        # 多样性分析
        _t("alpha-data", "Alpha多样性指数计算", ["ASV_TABLE_EVEN", "ROOTED_TREE"], ["ALPHA_INDEX"], "多样性分析"),
        _t("beta-data", "Beta多样性距离计算", ["ASV_TABLE_EVEN", "ROOTED_TREE"], ["DIST_MATRIX", "PCOA_COORDS"], "多样性分析"),
        _t("upgma", "UPGMA聚类树构建", ["ASV_TABLE_EVEN", "TREE_NWK"], ["UPGMA_TREE", "DIST_MATRIX", "PCOA_COORDS"], "多样性分析"),
        _t("alpha-div", "Alpha多样性显著性检验", ["ALPHA_INDEX"], ["ALPHA_SIG"], "多样性分析"),
        _t("alpha-rarefaction", "Alpha稀疏曲线", ["ASV_TABLE_EVEN"], ["RAREFACTION_CURVE"], "多样性分析"),
        _t("beta-div", "Beta多样性显著性检验", ["DIST_MATRIX"], ["BETA_SIG"], "多样性分析"),
        # 统计检验
        _t("catecomp", "群落差异多变量统计检验", ["ASV_TABLE_EVEN", "DIST_MATRIX"], ["CATECOMP_RESULT"], "统计检验"),
        _t("lefse", "LEfSe生物标志物发现", ["RELATIVE_ABUNDANCE"], ["LEFSE_RESULT"], "统计检验"),
        _t("metastat", "MetaStat组间差异物种分析", ["EVEN_ABS_ABUNDANCE"], ["METASTAT_RESULT"], "统计检验"),
        _t("randomforest", "随机森林分类", ["RELATIVE_ABUNDANCE"], ["RF_RESULT"], "统计检验"),
        _t("simper", "SIMPER相似性百分比分析", ["RELATIVE_ABUNDANCE"], ["SIMPER_RESULT"], "统计检验"),
        _t("ttest", "T检验与Wilcoxon检验", ["RELATIVE_ABUNDANCE"], ["TTEST_RESULT"], "统计检验"),
        # 可视化
        _t("top-species", "Top10优势物种柱状图", ["RELATIVE_ABUNDANCE"], ["TOP_SPECIES"], "可视化"),
        _t("genus-tree", "属水平系统发育树", ["TAXONOMY_ASSIGN", "RELATIVE_ABUNDANCE", "FEATURE_FASTA"], ["GENUS_TREE"], "可视化"),
        _t("krona", "Krona交互式分类组成图", ["ASV_TABLE_EVEN"], ["KRONA_CHART"], "可视化"),
        _t("network", "2D微生物共发生网络", ["RELATIVE_ABUNDANCE"], ["NETWORK_2D"], "可视化"),
        _t("network3d", "3D微生物网络可视化", ["RELATIVE_ABUNDANCE"], ["NETWORK_3D"], "可视化"),
        _t("otutree", "OTU系统发育树热图", ["UPGMA_TREE", "RELATIVE_ABUNDANCE"], ["OTU_TREE"], "可视化"),
        _t("taxasummary", "物种组成热图(样本)", ["RELATIVE_ABUNDANCE"], ["TAXA_HEATMAP"], "可视化"),
        _t("taxasummary-group", "物种组成热图(分组)", ["GROUP_REL_ABUNDANCE"], ["TAXA_GROUP_HEATMAP"], "可视化"),
        _t("ternary", "三元相图", ["GROUP_REL_ABUNDANCE"], ["TERNARY_CHART"], "可视化"),
        _t("venn", "Venn图分析", ["GROUP_EVEN_TABLE"], ["VENN_CHART"], "可视化"),
        # 排序分析
        _t("pca", "PCA主成分分析", ["RELATIVE_ABUNDANCE"], ["PCA_PLOT"], "排序分析"),
        _t("pcoa", "PCoA主坐标分析", ["PCOA_COORDS"], ["PCOA_PLOT"], "排序分析"),
        _t("nmds", "NMDS非度量多维标度", ["ASV_TABLE_EVEN"], ["NMDS_PLOT"], "排序分析"),
        _t("dca", "DCA去趋势对应分析", ["ASV_TABLE_EVEN"], ["DCA_PLOT"], "排序分析"),
        # 功能预测
        _t("funpre", "PICRUSt2功能预测", ["FEATURE_TABLE", "FEATURE_FASTA"], ["FUNC_PREDICTION"], "功能预测"),
    ]
