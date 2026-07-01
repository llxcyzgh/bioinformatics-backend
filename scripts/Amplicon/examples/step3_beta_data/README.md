# step3_beta_data 示例数据

## 输入文件

- `asv_table.even.txt` - 均一化 ASV 表（637K，12 样本）
- `rooted-tree.qza` - 有根系统发育树（必需）
- `alpha.mf` - 样本元数据（表头 `#SampleID\tDescription`）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_beta_data.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_beta_data/asv_table.even.txt" \
    -t "${AMPLICON_ROOT}/v2/examples/step3_beta_data/rooted-tree.qza" \
    -m "${AMPLICON_ROOT}/v2/examples/step3_beta_data/alpha.mf" \
    -o BetaData_Output/
```

## 示例来源

- `rooted-tree.qza`、`alpha.mf` 复制自：`/grj/BioAgent/test/Phylogeny/`、`/grj/BioAgent/test/alpha.mf`

## 输出

- `*_distance_matrix.qza`、`*_pcoa_results_qza/ordination.txt` → 供 `step5_pcoa.sh` 使用
