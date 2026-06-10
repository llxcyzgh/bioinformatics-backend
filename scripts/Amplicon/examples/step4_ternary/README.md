# step4_ternary 示例数据

## 输入文件

- `Relative_group/` - 分组相对丰度表目录（7 个文件，84K）
  - `asv_table.*.relative.xls` - 各分类层级（k/p/c/o/f/g/s）
- `ternary.list` - 三元相图分组列表（70B, 2 组三元对比）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step4_ternary"
bash "${AMPLICON_ROOT}/scripts/step4_ternary.sh" -i Relative_group/ -l ternary.list
```

## 输出

- `*.svg` - 三元相图（SVG 格式）
- `*.png` - 三元相图（PNG 格式）

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step4_ternary/Relative_group/`
- 输入：`${AMPLICON_ROOT}/examples/step4_ternary/ternary.list`
- 输出：`${AMPLICON_ROOT}/examples/step4_ternary/`（或由 `-o` 指定）
