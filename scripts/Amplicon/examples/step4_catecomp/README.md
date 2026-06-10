# step4_catecomp 示例数据

## 输入文件

- `asv_table.even.txt` - 均一化 ASV 表（7.9K）
- `group.list` - 样本分组文件（20 个样本）
- `unweighted_unifrac_dm.txt` - Unweighted UniFrac 距离矩阵（18K，可选）
- `weighted_unifrac_dm.txt` - Weighted UniFrac 距离矩阵（18K，可选）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step4_catecomp"
bash "${AMPLICON_ROOT}/scripts/step4_catecomp.sh" -t asv_table.even.txt -g group.list -u unweighted_unifrac_dm.txt -w weighted_unifrac_dm.txt
```

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step4_catecomp/asv_table.even.txt`
- 输入：`${AMPLICON_ROOT}/examples/step4_catecomp/group.list`
- 输入：`${AMPLICON_ROOT}/examples/step4_catecomp/unweighted_unifrac_dm.txt`
- 输出：`${AMPLICON_ROOT}/examples/step4_catecomp/`（或由 `-o` 指定）
