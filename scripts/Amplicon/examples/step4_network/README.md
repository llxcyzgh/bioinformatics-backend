# step4_network 示例数据

## 输入文件

- `genus.relative.xls` - 属水平相对丰度表
- `group.list` - 样本分组（12 样本，T100/T200/T109/T209）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_network.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_network/genus.relative.xls" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_network/group.list" \
    -o Network_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/Relative/asv_table.g.relative.xls`

## 输出

- 每组子目录 `{group}/dot/` 网络图与计算结果
