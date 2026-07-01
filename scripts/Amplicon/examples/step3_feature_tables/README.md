# step3_feature_tables 示例数据

## 输入文件

- `featureTable.biom` - ASV 丰度表（BIOM）
- `all_tax_assignments.txt` - VSEARCH 物种注释结果

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_feature_tables.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_feature_tables/featureTable.biom" \
    -t "${AMPLICON_ROOT}/v2/examples/step3_feature_tables/all_tax_assignments.txt" \
    -o FeatureTables_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/ConstructASV/featureTable.biom`
- 复制自：`/grj/BioAgent/test/Taxassign/all_tax_assignments.txt`

## 输出

- `asv_table.txt` → 供 `step3_table_stats.sh` 使用
