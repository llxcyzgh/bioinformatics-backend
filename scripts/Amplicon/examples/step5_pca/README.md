# step5_pca 示例数据

## 输入文件

| 文件/目录 | 说明 |
|-----------|------|
| `Relative/` | 各分类层级相对丰度表目录（推荐，8 个 `.xls`） |
| `asv_table.even.txt` | 均一化 ASV 表（脚本内自动生成 `Relative/`） |
| `Relative/asv_table.g.relative.xls` | 也可直接传入单个层级表 |
| `group.list` | 样本分组（12 样本，T100/T200/T109/T209） |

## 测试命令

```bash
# 方式 1：Relative 目录（默认属水平 genus）
bash "${AMPLICON_ROOT}/v2/scripts/step5_pca.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_pca/Relative/" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_pca/group.list" \
    -o PCA_Output/

# 方式 2：均一化 ASV 表
bash "${AMPLICON_ROOT}/v2/scripts/step5_pca.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_pca/asv_table.even.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_pca/group.list" \
    -l genus \
    -o PCA_Output/

# 方式 3：指定多个层级
bash "${AMPLICON_ROOT}/v2/scripts/step5_pca.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_pca/Relative/" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_pca/group.list" \
    -l genus,phylum \
    -o PCA_Output/

# 方式 4：单个相对丰度表
bash "${AMPLICON_ROOT}/v2/scripts/step5_pca.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step5_pca/Relative/asv_table.g.relative.xls" \
    -g "${AMPLICON_ROOT}/v2/examples/step5_pca/group.list" \
    -o PCA_Output/
```

## 示例来源

- `Relative/`、`asv_table.even.txt`、`group.list` 复制自：`/grj/BioAgent/test/TableStats/`

## 说明

- 也支持 `-i asv_table.even.txt`（脚本内自动生成 `Relative/`）；本目录提供现成的 `Relative/` 便于直接试跑。
- `group_col.list` 由脚本内 `color_defined.pl` 自动生成，无需手动提供。

## 输出

- `PCA.{level}.svg/png/pdf`（如 `PCA.genus.pdf`）
