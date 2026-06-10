# step3_genus_tree 示例数据

## 输入文件

- `all_tax_assignments.txt` - 物种注释表（2.7K, 20 条序列）
- `asv_table.g.relative.xls` - 属水平相对丰度表（14K）
- `feature.fasta` - ASV 代表序列（8.3K, 20 条序列）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step3_genus_tree"
bash "${AMPLICON_ROOT}/scripts/step3_genus_tree.sh" -t all_tax_assignments.txt -g asv_table.g.relative.xls -s feature.fasta
```

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step3_genus_tree/all_tax_assignments.txt`
- 输入：`${AMPLICON_ROOT}/examples/step3_genus_tree/asv_table.g.relative.xls`
- 输入：`${AMPLICON_ROOT}/examples/step3_genus_tree/feature.fasta`
