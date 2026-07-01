# step3_taxonomy 示例数据

## 输入文件

- `feature.fasta` - ASV 代表序列（FASTA，来自 test ConstructASV）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_taxonomy.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_taxonomy/feature.fasta" \
    -t 16S \
    -p 8 \
    -o Taxonomy_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/ConstructASV/feature.fasta`

## 说明

- 也可传入 `featureSeqs.qza`（见 `step3_phylogeny/` 示例）。
- 参考数据库路径由脚本/环境配置，非本目录示例文件。

## 输出

- `all_tax_assignments.txt`、`seq_taxonomy.qza` 等
