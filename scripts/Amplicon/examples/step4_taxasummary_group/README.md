# step4_taxasummary_group 示例数据

## 输入文件

| 文件/目录 | 说明 |
|-----------|------|
| `Relative_group/` | 分组相对丰度表（6 个层级 `.xls`，推荐） |
| `asv_table.even.txt` | 均一化 ASV 表（脚本内生成 `Relative/` 与 `Relative_group/`） |
| `group.list` | 样本分组（`-i` 为 even 或 Relative/ 时必需） |

## 测试命令

```bash
# 方式 1：Relative_group 目录
bash "${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_taxasummary_group/Relative_group/" \
    -o TaxaSummaryGroup_Output/

# 方式 2：均一化 ASV 表
bash "${AMPLICON_ROOT}/v2/scripts/step4_taxasummary_group.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_taxasummary_group/asv_table.even.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_taxasummary_group/group.list" \
    -l genus \
    -o TaxaSummaryGroup_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/`

## 输出

- `cluster.{level}.png/pdf` 等分组物种组成热图
