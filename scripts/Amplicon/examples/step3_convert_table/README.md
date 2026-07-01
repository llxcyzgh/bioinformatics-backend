# step3_convert_table 示例数据

## 输入文件

| 文件 | 用途（`-t` 类型） |
|------|-------------------|
| `featureTable.biom` | BIOM → QZA |
| `asv_table.txt` | TSV 特征表 → QZA |
| `asv_table.even.txt` | 均一化 TSV → QZA |

## 测试命令

```bash
# BIOM 转换
bash "${AMPLICON_ROOT}/v2/scripts/step3_convert_table.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_convert_table/featureTable.biom" \
    -t biom \
    -o ConvertTable_Output/

# TSV 转换
bash "${AMPLICON_ROOT}/v2/scripts/step3_convert_table.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_convert_table/asv_table.even.txt" \
    -t tsv \
    -o ConvertTable_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/ConstructASV/`、`FeatureTable/`、`TableStats/`
