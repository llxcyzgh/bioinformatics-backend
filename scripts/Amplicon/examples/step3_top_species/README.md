# step3_top_species 示例数据

## 输入文件

- `Relative/` - 各分类层级相对丰度表目录（7 个 `.xls` 文件）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step3_top_species.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step3_top_species/Relative/" \
    -g "${AMPLICON_ROOT}/v2/examples/step3_top_species/group.list" \
    -o TopSpecies_Output/
```

## 输出

- `top10/asv_table.p10.relative.xls` 等 → 供 `step4_otutree.sh` 使用
