# step3_genus_tree 示例数据

## 输入文件

- `all_tax_assignments.txt` - 物种注释表
- `asv_table.g.relative.xls` - 属水平相对丰度表（样本）
- `asv_table.relative.xls` - 样本相对丰度表（select_OTUs 用）
- `asv_table.txt` - ASV 特征表
- `feature.fasta` - ASV 代表序列

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_genus_tree.sh" \
    -t "${AMPLICON_ROOT}/v2/examples/step3_genus_tree/all_tax_assignments.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step3_genus_tree/asv_table.g.relative.xls" \
    -r "${AMPLICON_ROOT}/v2/examples/step3_genus_tree/asv_table.relative.xls" \
    -a "${AMPLICON_ROOT}/v2/examples/step3_genus_tree/asv_table.txt" \
    -s "${AMPLICON_ROOT}/v2/examples/step3_genus_tree/feature.fasta" \
    -o GenusTree_Output/
```

## 示例来源

- `asv_table.txt`、`asv_table.relative.xls` 复制自：`/grj/BioAgent/test/FeatureTable/`、`TableStats/Relative/`
