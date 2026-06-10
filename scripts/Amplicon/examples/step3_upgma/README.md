# step3_upgma 示例数据

## 输入文件

- `asv_table.even.txt` - 均一化 ASV 表（软链接到 step3_alpha_data）
- `rooted-tree.nwk` - 有根系统发育树（Newick 格式，648K）
- `alpha.mf` - 样本元数据文件（25 个样本）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step3_upgma"
bash "${AMPLICON_ROOT}/scripts/step3_upgma.sh" -i asv_table.even.txt -t rooted-tree.nwk -m alpha.mf
```

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step3_upgma/asv_table.even.txt`
- 输入：`${AMPLICON_ROOT}/examples/step3_upgma/rooted-tree.nwk`
- 输入：`${AMPLICON_ROOT}/examples/step3_upgma/alpha.mf`
