# step5_pcoa 示例数据

## 输入文件

| 文件/目录 | 说明 | 是否必需 |
|-----------|------|----------|
| `BetaData/` | 含 `*_pcoa_results_qza/ordination.txt`（来自 step3_beta_data） | **推荐**（`-i`） |
| `group.list` | 样本分组 | **必需**（`-g`） |

> **不需要** `*_dm.txt`（距离矩阵属于 `step5_beta_div.sh` / `step4_catecomp.sh`）。  
> **不需要** `group_col.list`（脚本内自动调用 `color_defined.pl` 生成）。

## 测试命令

```bash
# 推荐：传入 BetaData 目录
bash "${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_pcoa/BetaData/" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_pcoa/group.list" \
    -o PCoA_Output/

# 指定距离
bash "${AMPLICON_ROOT}/v2/scripts/step5_pcoa.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_pcoa/BetaData/" \
    -d weighted_unifrac,jaccard \
    -g "${AMPLICON_ROOT}/v2/examples/step5_pcoa/group.list" \
    -o PCoA_Output/
```

## 示例来源

- `BetaData/*/ordination.txt` 复制自：`/grj/BioAgent/test/BetaData/`
- `group.list` 复制自：`/grj/BioAgent/test/group.list`

## 输出

- `{distance}/PCoA12.pdf`、`{distance}/PCoA12.png`（如 `weighted_unifrac/PCoA12.pdf`）
