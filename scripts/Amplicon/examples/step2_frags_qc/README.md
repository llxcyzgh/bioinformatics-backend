# step2_frags_qc 示例数据

## 输入文件

- `T1001.extendedFrags.fastq` - FLASH 拼接后的序列

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step2_frags_qc.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step2_frags_qc/T1001.extendedFrags.fastq" \
    -o FragsQC_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/QC/T1001.extendedFrags.fastq`

## 下游

- 质控后 fastq 写入 `manifest.tsv`，供 `step3_dada2.sh` 使用
