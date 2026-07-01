# step3_alpha_data 示例数据

## 输入文件

- `asv_table.even.txt` - 均一化 ASV 表（637K，12 样本）
- `rooted-tree.qza` - 有根系统发育树
- `alpha.mf` - 样本元数据（表头 `#SampleID\tDescription`）

## 测试命令

```bash
# 仅 Alpha 指数
bash "${AMPLICON_ROOT}/v2/scripts/step3_alpha_data.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_alpha_data/asv_table.even.txt" \
    -o AlphaData_Output/

# Alpha 指数 + 稀化曲线
bash "${AMPLICON_ROOT}/v2/scripts/step3_alpha_data.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_alpha_data/asv_table.even.txt" \
    -t "${AMPLICON_ROOT}/v2/examples/step3_alpha_data/rooted-tree.qza" \
    -m "${AMPLICON_ROOT}/v2/examples/step3_alpha_data/alpha.mf" \
    -o AlphaData_Output/
```

## 示例来源

- `rooted-tree.qza`、`alpha.mf` 复制自：`/grj/BioAgent/test/Phylogeny/`、`/grj/BioAgent/test/alpha.mf`
