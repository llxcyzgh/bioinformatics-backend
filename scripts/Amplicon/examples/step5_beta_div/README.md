# step5_beta_div 示例数据

## 输入文件

- `unweighted_unifrac_dm.txt` - 非加权 UniFrac 距离矩阵
- `weighted_unifrac_dm.txt` - 加权 UniFrac 距离矩阵
- `group.list` - 样本分组（12 样本）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step5_beta_div.sh" \
    -u "${AMPLICON_ROOT}/v2/examples/step5_beta_div/unweighted_unifrac_dm.txt" \
    -w "${AMPLICON_ROOT}/v2/examples/step5_beta_div/weighted_unifrac_dm.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_beta_div/group.list" \
    -o BetaDiv_Output/
```

## 示例来源

- 距离矩阵：`/grj/BioAgent/test/UPGMA/PCoA_data/`
- `group.list`：`/grj/BioAgent/test/group.list`

## 说明

- 距离矩阵来自 UPGMA/Beta 分析流程，与 `step4_catecomp` 示例同源。
- 不需要 `group_col.list`（脚本内自动生成）。

## 输出

- `beta_div/`、`unweighted_unifrac_wilcox.txt`、`weighted_unifrac_wilcox.txt` 等
