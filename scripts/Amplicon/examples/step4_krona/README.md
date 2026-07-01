# step4_krona 示例数据

## 输入文件

- `asv_table.even.txt` - 均一化 ASV 表（含分类学信息，12 样本）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_krona.sh" \
    -t "${AMPLICON_ROOT}/v2/examples/step4_krona/asv_table.even.txt" \
    -o Krona_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/TableStats/asv_table.even.txt`

## 输出

- `krona.html` 及 Krona 资源文件
