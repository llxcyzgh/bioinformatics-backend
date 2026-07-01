# step4_network3d 示例数据

## 输入文件

- `genus.relative.xls` - 属水平相对丰度表

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_network3d.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_network3d/genus.relative.xls" \
    -n 50 \
    -o Network3D_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/Relative/asv_table.g.relative.xls`（作 `genus.relative.xls`）

## 输出

- `map.txt`、`edgeplot.xls`、`node.xls`、`network3D.html`（若环境支持）
