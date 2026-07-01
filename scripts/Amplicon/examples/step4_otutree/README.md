# step4_otutree 示例数据

## 输入文件

- `asv_table.even_weighted_unifrac_upgma.tre` - Weighted UniFrac UPGMA 树（来自 step3_upgma）
- `asv_table.even_unweighted_unifrac_upgma.tre` - Unweighted UniFrac UPGMA 树
- `top10_asv_table.p.relative.xls` - 门水平 Top10 物种丰度表（来自 step3_top_species）
- `group.list` - 样本分组（可选，用于树图分组着色）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_otutree.sh" \
    -w "${AMPLICON_ROOT}/v2/examples/step4_otutree/asv_table.even_weighted_unifrac_upgma.tre" \
    -u "${AMPLICON_ROOT}/v2/examples/step4_otutree/asv_table.even_unweighted_unifrac_upgma.tre" \
    -r "${AMPLICON_ROOT}/v2/examples/step4_otutree/top10_asv_table.p.relative.xls" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_otutree/group.list" \
    -o OTUTree_Output/
```

## 示例来源

- UPGMA 树：`/grj/BioAgent/test/UPGMA/`
- Top10 表：`/grj/BioAgent/test/top10/top10/`

## 输出

- `UPGMA.W.tree.svg/png`、`UPGMA.UnW.tree.svg/png`

## 相关文档

- **模块说明**: [`v2/reference/step4_otutree.md`](../../reference/step4_otutree.md)
- **上游**: [`step3_upgma`](../step3_upgma/README.md)、[`step3_top_species`](../step3_top_species/README.md)
