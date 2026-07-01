# step1_cutadapt 示例数据

## 输入文件

- `T1001.R1.fastq.gz` - 原始双端测序正向 reads（UOP25100039 项目）
- `T1001.R2.fastq.gz` - 原始双端测序反向 reads

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step1_cutadapt.sh" \
    -r1 "${AMPLICON_ROOT}/v2/examples/step1_cutadapt/T1001.R1.fastq.gz" \
    -r2 "${AMPLICON_ROOT}/v2/examples/step1_cutadapt/T1001.R2.fastq.gz" \
    -f GTGCCAGCMGCCGCGGTAA \
    -r GGACTACHVGGGTWTCTAAT \
    -o Cutadapt_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/shared/T1001.R{1,2}.fastq.gz`（原始测序）
