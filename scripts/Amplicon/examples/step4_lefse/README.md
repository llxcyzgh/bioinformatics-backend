# step4_lefse 示例数据

## 输入文件

| 文件/目录 | 说明 |
|-----------|------|
| `Relative/` | 各分类层级相对丰度表（推荐） |
| `asv_table.even.txt` | 均一化 ASV 表（脚本内自动生成 `Relative/`） |
| `all.mf` | 样本元数据 |
| `lefse_vs.list` | LEfSe 对比列表 |

## 测试命令

```bash
# 方式 1：Relative 目录
bash "${AMPLICON_ROOT}/v2/scripts/step4_lefse.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_lefse/Relative/" \
    -m "${AMPLICON_ROOT}/v2/examples/step4_lefse/all.mf" \
    -v "${AMPLICON_ROOT}/v2/examples/step4_lefse/lefse_vs.list" \
    -o LEfSe_Output/

# 方式 2：均一化 ASV 表
bash "${AMPLICON_ROOT}/v2/scripts/step4_lefse.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_lefse/asv_table.even.txt" \
    -m "${AMPLICON_ROOT}/v2/examples/step4_lefse/all.mf" \
    -v "${AMPLICON_ROOT}/v2/examples/step4_lefse/lefse_vs.list" \
    -o LEfSe_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/`、`alpha.mf`（作 `all.mf`）

## 输出

- `LDA.png/pdf`、`LEfSe.png/pdf` 等
