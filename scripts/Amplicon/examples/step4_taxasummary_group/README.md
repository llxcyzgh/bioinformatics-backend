# step4_taxasummary_group 示例数据

## 输入文件

- `Relative_group/` - 分组相对丰度表目录（6 个分类层级，76K）
  - `asv_table_group.p.relative.xls` - 门水平（9.0K）
  - `asv_table_group.c.relative.xls` - 纲水平（12K）
  - `asv_table_group.o.relative.xls` - 目水平（14K）
  - `asv_table_group.f.relative.xls` - 科水平（14K）
  - `asv_table_group.g.relative.xls` - 属水平（14K）
  - `asv_table_group.s.relative.xls` - 种水平（6.9K）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step4_taxasummary_group"
bash "${AMPLICON_ROOT}/scripts/step4_taxasummary_group.sh" -i Relative_group/
```

## 输出

- `cluster/cluster.*.png/pdf` - 各层级分组物种组成热图（p/c/o/f/g/s）

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step4_taxasummary_group/Relative_group/`
- 输出：`${AMPLICON_ROOT}/examples/step4_taxasummary_group/`（或由 `-o` 指定）
