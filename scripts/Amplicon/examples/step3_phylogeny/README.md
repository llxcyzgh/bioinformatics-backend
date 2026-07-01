# step3_phylogeny 示例数据

## 输入文件

- `featureSeqs.qza` - ASV 代表序列（QIIME2）
- `sequences.fasta` - ASV 代表序列（FASTA，与 qza 同源）
- `rooted-tree.qza` / `unrooted-tree.qza` - 预构建树（参考输出，也可仅作下游 beta/upgma 输入）
- `rooted_tree.nwk` / `unrooted_tree.nwk` - Newick 格式树

## 测试命令

```bash
# 从 QZA 构建（需 QIIME2 环境，耗时较长）
bash "${AMPLICON_ROOT}/v2/scripts/step3_phylogeny.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_phylogeny/featureSeqs.qza" \
    -n 4 \
    -o Phylogeny_Output/

# 或从 FASTA 输入
bash "${AMPLICON_ROOT}/v2/scripts/step3_phylogeny.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_phylogeny/sequences.fasta" \
    -n 4 \
    -o Phylogeny_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/ConstructASV/`、`/grj/BioAgent/test/Phylogeny/`

## 下游

- `rooted-tree.qza` → `step3_beta_data.sh`、`step3_alpha_data.sh`
- `rooted_tree.nwk` → `step3_upgma.sh`
