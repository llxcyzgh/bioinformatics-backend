# step1_flash 示例数据

## 输入文件

- `T1001_R1.fastq.gz` - cutadapt 后正向 reads
- `T1001_R2.fastq.gz` - cutadapt 后反向 reads

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step1_flash.sh" \
    -1 "${AMPLICON_ROOT}/v2/examples/step1_flash/T1001_R1.fastq.gz" \
    -2 "${AMPLICON_ROOT}/v2/examples/step1_flash/T1001_R2.fastq.gz" \
    -o Flash_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/QC/T1001.cutadapt.R{1,2}.fastq.gz`

## 下游

- 输出 `T1001.extendedFrags.fastq` → `step2_frags_qc.sh`
