# step4_metastat 示例数据

## 输入文件

- `asv_table.even.txt` - 均一化 ASV 表（脚本内生成各层级 even 绝对丰度）
- `group.list` - 样本分组（12 样本）
- `Vs.list` - 对比组列表（`T100_vs_T200`、`T109_vs_T209`）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_metastat.sh" \
    -e "${AMPLICON_ROOT}/v2/examples/step4_metastat/asv_table.even.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_metastat/group.list" \
    -v "${AMPLICON_ROOT}/v2/examples/step4_metastat/Vs.list" \
    -l genus,phylum \
    -o MetaStat_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/`、`vs.list`（转为 `Vs.list`）

## 输出

- `{level}/metastat_*.txt`、箱线图等
