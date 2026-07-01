# step3_upgma 示例数据

## 输入文件

| 文件 | 说明 |
|------|------|
| `asv_table.even.txt` | 样本均一化 ASV 表 |
| `rooted-tree.nwk` | 有根系统发育树（Newick） |
| `alpha.mf` | 样本元数据（`#SampleID\tDescription`） |
| `asv_table.group.even.txt` | 分组均一化表（可选，`-G`） |
| `BetaData/` | PCoA ordination（可选，软链至 `step5_pcoa/BetaData/`） |

## 测试命令

```bash
# 样本 UPGMA
bash "${AMPLICON_ROOT}/v2/scripts/step3_upgma.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_upgma/asv_table.even.txt" \
    -t "${AMPLICON_ROOT}/v2/examples/step3_upgma/rooted-tree.nwk" \
    -m "${AMPLICON_ROOT}/v2/examples/step3_upgma/alpha.mf" \
    -o UPGMA_Output/

# 样本 + 分组 UPGMA，并引用 BetaData PCoA 坐标
bash "${AMPLICON_ROOT}/v2/scripts/step3_upgma.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_upgma/asv_table.even.txt" \
    -t "${AMPLICON_ROOT}/v2/examples/step3_upgma/rooted-tree.nwk" \
    -m "${AMPLICON_ROOT}/v2/examples/step3_upgma/alpha.mf" \
    -G "${AMPLICON_ROOT}/v2/examples/step3_upgma/asv_table.group.even.txt" \
    --unweighted-pcoa "${AMPLICON_ROOT}/v2/examples/step3_upgma/BetaData/unweighted_unifrac_pcoa_results_qza/ordination.txt" \
    --weighted-pcoa "${AMPLICON_ROOT}/v2/examples/step3_upgma/BetaData/weighted_unifrac_pcoa_results_qza/ordination.txt" \
    -o UPGMA_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/`、`Phylogeny/`、`alpha.mf`
- `BetaData/` → 软链接 `../step5_pcoa/BetaData/`

## 输出

- `UPGMA_sample/`、`UPGMA_group/`（提供 `-G` 时）、`PCoA_data/` 等
