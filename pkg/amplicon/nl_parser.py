"""
自然语言 → PlanningRequest 解析器（关键词回退）

基于关键词匹配，将用户分析需求转换为可用输入 + 目标输出。
当无法识别时返回空列表，由上层决定是否追问用户。
"""

from __future__ import annotations


def _match(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)


def parse_natural_language(user_input: str) -> dict:
    t = user_input.lower()

    # ─── 识别用户拥有的数据 ────────────────────────────
    available_inputs: list[str] = []

    has_fastq = _match(t, ["双端", "paired", "fastq", "原始数据", "raw", "测序数据", "下机数据", "16s", "its", "18s", "扩增子"])
    has_fasta = _match(t, ["fasta", "fna", "序列文件"])
    has_asv = _match(t, ["asv", "otu", "特征表", "feature table", "已做完去噪", "已做完dada2", "denoise"])
    has_qc = _match(t, ["已做完质控", "质控后", "qc后"])
    has_trimmed = _match(t, ["已切除引物", "切完引物", "trimmed"])
    has_merged = _match(t, ["已拼接", "merged"])

    if has_asv:
        available_inputs = ["FEATURE_SEQS", "FEATURE_TABLE", "FEATURE_FASTA"]
    elif has_qc:
        available_inputs = ["FASTQ_QC"]
    elif has_merged:
        available_inputs = ["FASTQ_MERGED"]
    elif has_trimmed:
        available_inputs = ["FASTQ_TRIMMED"]
    elif has_fasta and not has_fastq:
        available_inputs = ["FASTA_SEQ"]
    elif has_fastq:
        available_inputs = ["FASTQ_PAIR"]
    # else: 保持空列表，由上层追问

    # ─── 识别分析目标 ──────────────────────────────────
    goal_types: list[str] = []

    if _match(t, ["物种注释", "分类注释", "taxonomy", "物种分类", "注释"]):
        goal_types.append("TAXONOMY_ASSIGN")

    if _match(t, ["alpha", "α多样性", "丰富度", "shannon", "chao"]):
        goal_types += ["ALPHA_INDEX", "ALPHA_SIG"]

    if _match(t, ["beta", "β多样性", "群落结构", "样品距离"]):
        goal_types += ["DIST_MATRIX", "BETA_SIG"]

    if _match(t, ["多样性", "diversity"]) and not _match(t, ["alpha", "β", "beta"]):
        goal_types += ["ALPHA_INDEX", "ALPHA_SIG", "DIST_MATRIX", "BETA_SIG"]

    if _match(t, ["lefse", "生物标志物", "biomarker"]):
        goal_types.append("LEFSE_RESULT")
    if _match(t, ["metastat", "组间差异"]):
        goal_types.append("METASTAT_RESULT")
    if _match(t, ["随机森林", "random forest", " rf "]):
        goal_types.append("RF_RESULT")
    if _match(t, ["simper", "相似性"]):
        goal_types.append("SIMPER_RESULT")
    if _match(t, ["t检验", "t test", "wilcoxon", "秩和"]):
        goal_types.append("TTEST_RESULT")
    if _match(t, ["anosim", "adonis", "permanova", "amova", "mrpp", "多变量统计"]):
        goal_types.append("CATECOMP_RESULT")

    if _match(t, ["差异分析", "差异物种", "统计检验", "统计"]) and not _match(
        t, ["lefse", "metastat", "随机森林", "simper", "t检验", "anosim", "adonis"]
    ):
        goal_types += ["LEFSE_RESULT", "TTEST_RESULT"]

    if _match(t, ["网络", "network", "共发生"]):
        goal_types.append("NETWORK_2D")
    if _match(t, ["krona"]):
        goal_types.append("KRONA_CHART")
    if _match(t, ["热图", "heatmap", "热力图"]):
        goal_types.append("TAXA_HEATMAP")
    if _match(t, ["venn", "韦恩"]):
        goal_types.append("VENN_CHART")
    if _match(t, ["三元", "ternary"]):
        goal_types.append("TERNARY_CHART")
    if _match(t, ["柱状图", "top10", "优势物种"]):
        goal_types.append("TOP_SPECIES")
    if _match(t, ["系统发育树", "进化树", "发育树", "phylogen"]):
        goal_types.append("ROOTED_TREE")

    if _match(t, ["pca", "主成分"]):
        goal_types.append("PCA_PLOT")
    if _match(t, ["pcoa", "主坐标"]):
        goal_types.append("PCOA_PLOT")
    if _match(t, ["nmds"]):
        goal_types.append("NMDS_PLOT")
    if _match(t, ["排序", "ordination", "降维"]) and not _match(t, ["pca", "pcoa", "nmds"]):
        goal_types += ["PCA_PLOT", "PCOA_PLOT", "NMDS_PLOT"]

    if _match(t, ["功能预测", "picrust", "代谢通路", "kegg"]):
        goal_types.append("FUNC_PREDICTION")

    is_full = _match(t, ["全流程", "完整", "全套", "从头", "全部分析", "标准流程"])
    if is_full and not goal_types:
        goal_types = [
            "TAXONOMY_ASSIGN", "ALPHA_INDEX", "ALPHA_SIG",
            "DIST_MATRIX", "BETA_SIG", "TOP_SPECIES", "TAXA_HEATMAP",
        ]

    if _match(t, ["可视化", "图表", "绘图", "出图"]) and not goal_types:
        goal_types += ["TOP_SPECIES", "KRONA_CHART", "TAXA_HEATMAP"]

    goal_types = list(dict.fromkeys(goal_types))  # deduplicate preserving order

    # ─── 生成描述 ──────────────────────────────────────
    input_labels = {
        "FASTA_SEQ": "FASTA序列", "FASTQ_PAIR": "双端测序原始数据",
        "FASTQ_TRIMMED": "引物切除后数据", "FASTQ_MERGED": "已拼接序列",
        "FASTQ_QC": "质控后序列", "FEATURE_SEQS": "ASV序列",
        "FEATURE_TABLE": "ASV丰度表", "FEATURE_FASTA": "ASV序列文件",
    }
    goal_labels = {
        "TAXONOMY_ASSIGN": "物种注释", "ALPHA_INDEX": "Alpha多样性",
        "ALPHA_SIG": "Alpha检验", "DIST_MATRIX": "Beta多样性",
        "BETA_SIG": "Beta检验", "LEFSE_RESULT": "LEfSe分析",
        "METASTAT_RESULT": "MetaStat分析", "RF_RESULT": "随机森林",
        "SIMPER_RESULT": "SIMPER分析", "TTEST_RESULT": "T检验",
        "CATECOMP_RESULT": "群落差异检验", "TOP_SPECIES": "Top物种图",
        "KRONA_CHART": "Krona图", "TAXA_HEATMAP": "物种热图",
        "VENN_CHART": "Venn图", "NETWORK_2D": "网络图",
        "ROOTED_TREE": "系统发育树", "PCA_PLOT": "PCA",
        "PCOA_PLOT": "PCoA", "NMDS_PLOT": "NMDS",
        "FUNC_PREDICTION": "功能预测",
    }

    in_desc = "、".join(input_labels.get(i, i) for i in available_inputs)
    go_desc = "、".join(goal_labels.get(g, g) for g in goal_types[:5])

    scenario = ""
    if in_desc and go_desc:
        scenario = f"从{in_desc}出发，目标：{go_desc}"
    elif in_desc:
        scenario = f"已有数据：{in_desc}，待确定分析目标"
    elif go_desc:
        scenario = f"目标：{go_desc}，待确定输入数据"

    has_any_input = bool(has_fastq or has_fasta or has_asv or has_qc or has_trimmed or has_merged)
    confidence = "high" if has_any_input and goal_types else ("medium" if has_any_input or goal_types else "low")

    return {
        "available_inputs": available_inputs,
        "goal_types": goal_types,
        "scenario_description": scenario,
        "confidence": confidence,
    }
