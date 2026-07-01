# step0_import_fasta 示例数据

## 输入文件

- `sequences.fasta` - ASV 代表序列（FASTA，来自测试项目 ConstructASV）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step0_import_fasta.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step0_import_fasta/sequences.fasta" \
    -o ImportFasta_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/ConstructASV/feature.fasta`（重命名为 `sequences.fasta`）
