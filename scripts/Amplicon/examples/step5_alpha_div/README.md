# step5_alpha_div 示例数据

## 输入文件

- `alpha_diversity_index.txt` - Alpha 多样性指数表（12 样本）
- `group.list` - 样本分组

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step5_alpha_div.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_alpha_div/alpha_diversity_index.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_alpha_div/group.list" \
    -o AlphaDiv_Output/
```

## 示例来源

- `alpha_diversity_index.txt`：`/grj/BioAgent/test/AlphaData/alpha_index_table/`
- `group.list`：`/grj/BioAgent/test/group.list`

## 说明

- `group_col.list` 由脚本内自动生成。

## 输出

- `anova_test.txt`、`beeswarm/`、`alpha_diff.svg/png`
