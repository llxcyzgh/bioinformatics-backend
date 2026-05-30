"""
代码模板：每个工具 ID 映射到对应的脚本片段。
"""

TOOL_SCRIPT_TEMPLATES: dict[str, str] = {
    # 数据预处理
    "amp-import-fasta": """
# === FASTA导入QIIME2 ===
qiime tools import \\
  --type 'FeatureData[Sequences]' \\
  --input-path {input_fasta} \\
  --output-path {output_dir}/representative-sequences.qza
""",
    "amp-cutadapt": """
# === Cutadapt引物切除 ===
qiime cutadapt trim-paired \\
  --i-demultiplexed-sequences {input_fastq} \\
  --p-front-f {forward_primer} \\
  --p-front-r {reverse_primer} \\
  --o-trimmed-sequences {output_dir}/trimmed-demux.qza
""",
    "amp-flash": """
# === FLASH双端拼接 ===
flash {input_trimmed_R1} {input_trimmed_R2} \\
  -o {output_dir}/flash_merged
""",
    # 质量控制
    "amp-frags-qc": """
# === 序列质量控制 ===
# 质控参数根据数据特征调整
qiime quality-filter q-score-joined \\
  --i-demux {input_merged} \\
  --o-filtered-sequences {output_dir}/qc-sequences.qza \\
  --p-min-quality 20
""",
    # 核心分析
    "amp-dada2": """
# === DADA2 ASV推断与去噪 ===
qiime dada2 denoise-paired \\
  --i-demultiplexed-seqs {input_demux} \\
  --p-trunc-len-f 0 \\
  --p-trunc-len-r 0 \\
  --o-table {output_dir}/feature-table.qza \\
  --o-representative-sequences {output_dir}/rep-seqs.qza \\
  --o-denoising-stats {output_dir}/denoising-stats.qza
""",
    "amp-taxonomy": """
# === 物种分类注释 ===
qiime feature-classifier classify-sklearn \\
  --i-classifier {classifier_path} \\
  --i-reads {input_rep_seqs} \\
  --o-classification {output_dir}/taxonomy.qza
""",
    "amp-phylogeny": """
# === 系统发育树构建 ===
qiime phylogeny align-to-tree-mafft-fasttree \\
  --i-sequences {input_rep_seqs} \\
  --o-alignment {output_dir}/aligned-rep-seqs.qza \\
  --o-masked-alignment {output_dir}/masked-aligned-rep-seqs.qza \\
  --o-tree {output_dir}/unrooted-tree.qza \\
  --o-rooted-tree {output_dir}/rooted-tree.qza
""",
    "amp-feature-tables": """
# === ASV特征表构建（合并分类信息）===
qiime metadata tabulate \\
  --m-input-file {input_taxonomy} \\
  --o-visualization {output_dir}/taxonomy.qzv
qiime feature-table merge-taxinfo \\
  --i-table {input_feature_table} \\
  --i-taxonomy {input_taxonomy} \\
  --o-merged-table {output_dir}/asv-table-taxa.qza
""",
    "amp-table-stats": """
# === ASV表均一化与丰度计算 ===
qiime feature-table rarefy \\
  --i-table {input_asv_table} \\
  --p-sampling-depth {sampling_depth} \\
  --o-rarefied-table {output_dir}/even-table.qza
""",
    # 多样性分析
    "amp-alpha-data": """
# === Alpha多样性指数计算 ===
qiime diversity alpha \\
  --i-table {input_even_table} \\
  --p-metric shannon \\
  --o-alpha-diversity {output_dir}/shannon-index.qza
""",
    "amp-beta-data": """
# === Beta多样性距离计算 ===
qiime diversity beta \\
  --i-table {input_even_table} \\
  --p-metric braycurtis \\
  --o-distance-matrix {output_dir}/braycurtis-dist.qza
""",
    "amp-upgma": """
# === UPGMA聚类树构建 ===
qiime diversity beta \\
  --i-table {input_even_table} \\
  --p-metric weighted_unifrac \\
  --o-distance-matrix {output_dir}/weighted-unifrac-dist.qza
""",
    "amp-alpha-div": """
# === Alpha多样性显著性检验 ===
qiime diversity alpha-group-significance \\
  --i-alpha-diversity {input_alpha_index} \\
  --m-metadata-file {metadata_file} \\
  --o-visualization {output_dir}/alpha-significance.qzv
""",
    "amp-alpha-rarefaction": """
# === Alpha稀疏曲线 ===
qiime diversity alpha-rarefaction \\
  --i-table {input_even_table} \\
  --p-max-depth {max_depth} \\
  --m-metadata-file {metadata_file} \\
  --o-visualization {output_dir}/alpha-rarefaction.qzv
""",
    "amp-beta-div": """
# === Beta多样性显著性检验 ===
qiime diversity beta-group-significance \\
  --i-distance-matrix {input_dist_matrix} \\
  --m-metadata-file {metadata_file} \\
  --p-method permanova \\
  --o-visualization {output_dir}/beta-significance.qzv
""",
    # 统计检验
    "amp-lefse": """
# === LEfSe生物标志物发现 ===
# LEfSe分析（需R/Python环境）
lefse_run.py \\
  --input {input_rel_abundance} \\
  --metadata {metadata_file} \\
  --output {output_dir}/lefse_result
""",
    "amp-metastat": """
# === MetaStat组间差异物种分析 ===
metastat_run.py \\
  --input {input_even_abs_abundance} \\
  --metadata {metadata_file} \\
  --output {output_dir}/metastat_result
""",
    "amp-randomforest": """
# === 随机森林分类 ===
randomforest_run.py \\
  --input {input_rel_abundance} \\
  --metadata {metadata_file} \\
  --output {output_dir}/rf_result
""",
    "amp-simper": """
# === SIMPER相似性百分比分析 ===
simper_run.py \\
  --input {input_rel_abundance} \\
  --metadata {metadata_file} \\
  --output {output_dir}/simper_result
""",
    "amp-ttest": """
# === T检验与Wilcoxon检验 ===
ttest_run.py \\
  --input {input_rel_abundance} \\
  --metadata {metadata_file} \\
  --output {output_dir}/ttest_result
""",
    "amp-catecomp": """
# === 群落差异多变量统计检验 ===
catecomp_run.py \\
  --input {input_even_table} \\
  --dist-matrix {input_dist_matrix} \\
  --metadata {metadata_file} \\
  --output {output_dir}/catecomp_result
""",
    # 可视化
    "amp-top-species": """
# === Top10优势物种柱状图 ===
plot_top_species.py \\
  --input {input_rel_abundance} \\
  --output {output_dir}/top_species_barplot.pdf
""",
    "amp-genus-tree": """
# === 属水平系统发育树 ===
plot_genus_tree.py \\
  --taxonomy {input_taxonomy} \\
  --abundance {input_rel_abundance} \\
  --sequences {input_fasta} \\
  --output {output_dir}/genus_tree.pdf
""",
    "amp-krona": """
# === Krona交互式分类组成图 ===
plot_krona.py \\
  --input {input_even_table} \\
  --output {output_dir}/krona_chart.html
""",
    "amp-network": """
# === 2D微生物共发生网络 ===
plot_network.py \\
  --input {input_rel_abundance} \\
  --output {output_dir}/network_2d.pdf
""",
    "amp-network3d": """
# === 3D微生物网络可视化 ===
plot_network3d.py \\
  --input {input_rel_abundance} \\
  --output {output_dir}/network_3d.html
""",
    "amp-otutree": """
# === OTU系统发育树热图 ===
plot_otu_tree.py \\
  --tree {input_upgma_tree} \\
  --abundance {input_rel_abundance} \\
  --output {output_dir}/otu_tree_heatmap.pdf
""",
    "amp-taxasummary": """
# === 物种组成热图(样本) ===
plot_taxa_heatmap.py \\
  --input {input_rel_abundance} \\
  --output {output_dir}/taxa_heatmap.pdf
""",
    "amp-taxasummary-group": """
# === 物种组成热图(分组) ===
plot_taxa_heatmap_group.py \\
  --input {input_group_rel_abundance} \\
  --output {output_dir}/taxa_group_heatmap.pdf
""",
    "amp-ternary": """
# === 三元相图 ===
plot_ternary.py \\
  --input {input_group_rel_abundance} \\
  --output {output_dir}/ternary_plot.pdf
""",
    "amp-venn": """
# === Venn图分析 ===
plot_venn.py \\
  --input {input_group_even_table} \\
  --output {output_dir}/venn_diagram.pdf
""",
    # 排序分析
    "amp-pca": """
# === PCA主成分分析 ===
plot_pca.py \\
  --input {input_rel_abundance} \\
  --output {output_dir}/pca_plot.pdf
""",
    "amp-pcoa": """
# === PCoA主坐标分析 ===
qiime diversity pcoa \\
  --i-distance-matrix {input_pcoa_coords} \\
  --o-pcoa {output_dir}/pcoa.qza
qiime emperor plot \\
  --i-pcoa {output_dir}/pcoa.qza \\
  --m-metadata-file {metadata_file} \\
  --o-visualization {output_dir}/pcoa-plot.qzv
""",
    "amp-nmds": """
# === NMDS非度量多维标度 ===
plot_nmds.py \\
  --input {input_even_table} \\
  --output {output_dir}/nmds_plot.pdf
""",
    "amp-dca": """
# === DCA去趋势对应分析 ===
plot_dca.py \\
  --input {input_even_table} \\
  --output {output_dir}/dca_plot.pdf
""",
    # 功能预测
    "amp-funpre": """
# === PICRUSt2功能预测 ===
picrust2_pipeline.py \\
  --study-fasta {input_feature_fasta} \\
  --table {input_feature_table} \\
  --output {output_dir}/picrust2_output
""",
}

SCRIPT_HEADER = """#!/bin/bash
# BioFlow 自动生成分析脚本
# 生成时间: {timestamp}
# 工具链: {tool_chain_summary}

set -euo pipefail

OUTPUT_DIR="{output_dir}"
mkdir -p "$OUTPUT_DIR"

"""


def generate_workflow_script(tool_chain: list[dict]) -> str:
    """
    根据工具链生成组合脚本。
    tool_chain: [{id, name, category}, ...]
    """
    from datetime import datetime

    tool_names = " → ".join(t.get("name", t.get("id", "")) for t in tool_chain)
    header = SCRIPT_HEADER.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        tool_chain_summary=tool_names,
        output_dir="./bioflow_output",
    )

    parts = [header]
    for tool in tool_chain:
        tool_id = tool.get("id", "")
        template = TOOL_SCRIPT_TEMPLATES.get(tool_id)
        if template:
            parts.append(template.strip())
        else:
            parts.append(f"# === {tool.get('name', tool_id)} ===\n# TODO: 待补充脚本模板")

    return "\n\n".join(parts) + "\n"
