# step5_alpha_rarefaction 示例数据

## 输入文件

- `asv_table.even.txt` - 均一化 ASV 表
- `group.list` - 样本分组
- `alpha_index_table/observed_features.csv` - 运行前复制到输出目录（来自 step3_alpha_data）

> **不需要**在示例目录放置 `alpha.mf`、`group_col.list`（脚本未要求；颜色配置在输出目录内自动生成）。

## 测试命令

```bash
# 方式 1：将 alpha_index_table 复制到输出目录后运行
OUT=AlphaRarefaction_Output
mkdir -p "${OUT}"
cp -r "${AMPLICON_ROOT}/v2/examples/step5_alpha_rarefaction/alpha_index_table" "${OUT}/"

bash "${AMPLICON_ROOT}/v2/scripts/step5_alpha_rarefaction.sh" \
    -t "${AMPLICON_ROOT}/v2/examples/step5_alpha_rarefaction/asv_table.even.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_alpha_rarefaction/group.list" \
    -o "${OUT}/"
```

## 示例来源

- `alpha_index_table/observed_features.csv` 由 `/grj/BioAgent/test/AlphaData/alpha_index_table/observed_features_qza/alpha-diversity.tsv` 转换

## 输出

- `rank_abundance.svg/png`、`observed_features.svg/png`、`alpha_diversity.svg/png` 等
