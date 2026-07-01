# step4_ttest 示例数据

## 输入文件

- `Relative/` - 各分类层级相对丰度表（8 个 `.xls`）
- `group.list` - 样本分组（12 样本，T100/T200/T109/T209）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_ttest.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_ttest/Relative/" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_ttest/group.list" \
    --method wilcox \
    -o Ttest_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/Relative/`

## 输出

- 各层级 T 检验 / Wilcoxon 结果与图
