# PCA 示例数据

## 数据来源

- `asv_table.relative.xls`: `${AMPLICON_ROOT}/examples/step5_pca/asv_table.relative.xls`
- `group.list`: `${AMPLICON_ROOT}/examples/step5_pca/group.list`

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step5_pca"
bash "${AMPLICON_ROOT}/scripts/step5_pca.sh" -r asv_table.relative.xls -g group.list
```

## 输出

- `UOA_pca.svg`: PCA 排序图（SVG 格式）
- `UOA_pca.pdf`: PCA 排序图（PDF 格式）
- `UOA_pca.png`: PCA 排序图（PNG 格式）

## 说明

- 分组颜色配置（group_col.list）由脚本内部自动调用 `color_defined.pl` 生成
- 无需手动提供 group_col.list 文件
