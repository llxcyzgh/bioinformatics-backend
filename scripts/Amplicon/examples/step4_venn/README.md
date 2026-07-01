# step4_venn 示例数据

## 输入文件

| 文件 | 说明 |
|------|------|
| `asv_table.group.even.txt` | 分组均一化 ASV 表（推荐） |
| `asv_table.even.txt` | 样本 even 表（需配合 `-g` 生成 group even） |
| `group.list` | 样本分组（`-t` 为 even 表时使用） |
| `venn.G.list` | 维恩图分组列表（空格分隔：`T100 T200 T109 T209`） |

## 测试命令

```bash
# 方式 1：分组 even 表
bash "${AMPLICON_ROOT}/v2/scripts/step4_venn.sh" \
    -t "${AMPLICON_ROOT}/v2/examples/step4_venn/asv_table.group.even.txt" \
    -l "${AMPLICON_ROOT}/v2/examples/step4_venn/venn.G.list" \
    -o Venn_Output/

# 方式 2：样本 even 表 + group.list
bash "${AMPLICON_ROOT}/v2/scripts/step4_venn.sh" \
    -t "${AMPLICON_ROOT}/v2/examples/step4_venn/asv_table.even.txt" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_venn/group.list" \
    -l "${AMPLICON_ROOT}/v2/examples/step4_venn/venn.G.list" \
    -o Venn_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/`

## 输出

- `venn_display.png/pdf/svg` 等
