# step3_dada2 示例数据

## 输入文件

- `manifest.tsv` - 12 样本 QIIME2 manifest（绝对路径）
- `T1001.fastq` … `T2093.fastq` - 质控后序列（每样本约 3.3M）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_dada2.sh" \
    -m "${AMPLICON_ROOT}/v2/examples/step3_dada2/manifest.tsv" \
    -n 8 \
    -o DADA2_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/QC/T*.fastq`（12 样本）
- `manifest.tsv` 在复制后自动生成，路径指向本目录内 fastq

## 说明

- 若 clone 到其他机器，需重新生成 manifest 或批量替换第二列为本机绝对路径。
- 单样本快速试跑可只保留 `T1001.fastq` 并修改 manifest 仅含一行。
