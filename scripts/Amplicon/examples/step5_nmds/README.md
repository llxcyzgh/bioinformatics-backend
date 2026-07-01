# step5_nmds 示例数据

## 输入文件

| 文件/目录 | 说明 |
|-----------|------|
| `Relative/` | 各分类层级相对丰度表目录（推荐，8 个 `.xls`） |
| `asv_table.even.txt` | 均一化 ASV 表（脚本内自动生成 `Relative/`） |
| `group.list` | 样本分组（12 样本，T100/T200/T109/T209） |

## 测试命令

```bash
# 方式 1：Relative 目录（默认属水平 genus）
bash "${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_nmds/Relative/" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_nmds/group.list" \
    -o NMDS_Output/

# 方式 2：均一化 ASV 表
bash "${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_nmds/asv_table.even.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_nmds/group.list" \
    -l genus \
    -o NMDS_Output/

# 方式 3：单个相对丰度表
bash "${AMPLICON_ROOT}/v2/scripts/step5_nmds.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_nmds/Relative/asv_table.g.relative.xls" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_nmds/group.list" \
    -o NMDS_Output/
```

## 示例来源

- `Relative/`、`asv_table.even.txt`、`group.list` 复制自：`/grj/BioAgent/test/TableStats/`

## 说明

- `group_col.list` 可选；未提供时脚本根据 `group.list` 自动生成。

## 输出

- `NMDS.{level}.svg/png/pdf`、`NMDS.{level}_scores.txt`、`Stress.txt`
