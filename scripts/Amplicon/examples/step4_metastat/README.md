# step4_metastat 示例数据

## 输入文件

- `evenabs/` - 均一化绝对丰度表目录（6 个分类层级，76K）
  - `phylum/` - 门水平（9.0K）
  - `class/` - 纲水平（12K）
  - `order/` - 目水平（14K）
  - `family/` - 科水平（14K）
  - `genus/` - 属水平（14K）
  - `species/` - 种水平（6.9K）
- `group.list` - 样本分组文件（212B, 20 个样本）
- `Vs.list` - 对比组列表（71B, 2 组对比）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step4_metastat"
bash "${AMPLICON_ROOT}/scripts/step4_metastat.sh" -e evenabs/ -g group.list -v Vs.list
```

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step4_metastat/evenabs/`
- 输入：`${AMPLICON_ROOT}/examples/step4_metastat/group.list`
- 输入：`${AMPLICON_ROOT}/examples/step4_metastat/Vs.list`
- 输出：`${AMPLICON_ROOT}/examples/step4_metastat/`（或由 `-o` 指定）
