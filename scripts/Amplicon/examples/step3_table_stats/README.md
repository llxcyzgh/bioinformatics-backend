# step3_table_stats 示例数据

## 输入文件

- `asv_table.txt` - 标准化 ASV 特征表（758K，12 样本）
- `group.list` - 样本分组（T100/T200/T109/T209，各 3 重复）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_table_stats.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_table_stats/asv_table.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step3_table_stats/group.list" \
    -o TableStats_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/FeatureTable/asv_table.txt`、`/grj/BioAgent/test/group.list`

## 输出

- `asv_table.even.txt`、`Relative/`、`Relative_group/` 供 Step 4/5 多数模块使用
