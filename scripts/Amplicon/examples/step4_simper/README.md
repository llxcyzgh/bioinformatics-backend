# step4_simper 示例数据

## 输入文件

- `Relative/` - 各分类层级相对丰度表目录（7 个文件，84K）
  - `asv_table.k.relative.xls` - 界水平（1.4K）
  - `asv_table.p.relative.xls` - 门水平（9.0K）
  - `asv_table.c.relative.xls` - 纲水平（12K）
  - `asv_table.o.relative.xls` - 目水平（14K）
  - `asv_table.f.relative.xls` - 科水平（14K）
  - `asv_table.g.relative.xls` - 属水平（14K）
  - `asv_table.s.relative.xls` - 种水平（6.9K）
- `group.list` - 样本分组文件（212B, 20 个样本）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step4_simper"
bash "${AMPLICON_ROOT}/scripts/step4_simper.sh" -i Relative/ -g group.list
```

## 输出

- `*/simper_*.txt` - SIMPER 分析结果（6 个分类层级）

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step4_simper/Relative/`
- 输入：`${AMPLICON_ROOT}/examples/step4_simper/group.list`
- 输出：`${AMPLICON_ROOT}/examples/step4_simper/`（或由 `-o` 指定）
