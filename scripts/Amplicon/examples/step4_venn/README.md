# step4_venn 示例数据

## 输入文件

- `asv_table.group.even.txt` - 分组均一化 ASV 表（2.4K, 截取前 20 行）
- `venn.G.list` - 维恩图分组列表（4 个分组：D, DF, Y, Z）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step4_venn"
bash "${AMPLICON_ROOT}/scripts/step4_venn.sh" -t asv_table.group.even.txt -l venn.G.list
```

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step4_venn/asv_table.group.even.txt`
- 输入：`${AMPLICON_ROOT}/examples/step4_venn/venn.G.list`
- 输出：`${AMPLICON_ROOT}/examples/step4_venn/`（或由 `-o` 指定）
