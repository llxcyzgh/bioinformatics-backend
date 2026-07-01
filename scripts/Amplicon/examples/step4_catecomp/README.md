# step4_catecomp 示例数据

## 输入文件

- `asv_table.even.txt` - 均一化 ASV 表（12 样本）
- `group.list` - 样本分组
- `unweighted_unifrac_dm.txt` / `weighted_unifrac_dm.txt` - UniFrac 距离矩阵（可选，`-u/-w`）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_catecomp.sh" \
    -t "${AMPLICON_ROOT}/v2/examples/step4_catecomp/asv_table.even.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_catecomp/group.list" \
    -u "${AMPLICON_ROOT}/v2/examples/step4_catecomp/unweighted_unifrac_dm.txt" \
    -w "${AMPLICON_ROOT}/v2/examples/step4_catecomp/weighted_unifrac_dm.txt" \
    -o CateComp_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/`、`UPGMA/PCoA_data/`

## 输出

- `Anosim/`、`Adonis/`、`MRPP/`、`Amova/` 等统计结果
