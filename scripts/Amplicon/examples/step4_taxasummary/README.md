# step4_taxasummary 示例数据

## 输入文件

| 文件/目录 | 说明 |
|-----------|------|
| `Relative/` | 各分类层级相对丰度表（8 个 `.xls`，推荐） |
| `asv_table.even.txt` | 均一化 ASV 表（脚本内自动生成 `Relative/`） |
| `group.list` | 样本分组（12 样本） |

## 测试命令

```bash
# 方式 1：Relative 目录
bash "${AMPLICON_ROOT}/v2/scripts/step4_taxasummary.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_taxasummary/Relative/" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_taxasummary/group.list" \
    -o TaxaSummary_Output/

# 方式 2：均一化 ASV 表
bash "${AMPLICON_ROOT}/v2/scripts/step4_taxasummary.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_taxasummary/asv_table.even.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_taxasummary/group.list" \
    -l genus,phylum \
    -o TaxaSummary_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/`

## 输出

- `cluster.{level}.png/pdf` 等物种组成热图
