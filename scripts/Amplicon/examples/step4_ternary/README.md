# step4_ternary 示例数据

## 输入文件

- `Relative_group/` - 分组相对丰度表（6 个层级 `.xls`）
- `ternary.list` - 三元对比列表（如 `T100_T200_T109`）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_ternary.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_ternary/Relative_group/" \
    -l "${AMPLICON_ROOT}/v2/examples/step4_ternary/ternary.list" \
    -o Ternary_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/Relative_group/`

## 输出

- `*.svg`、`*.png` 三元相图
