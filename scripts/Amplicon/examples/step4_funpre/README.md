# step4_funpre 示例数据

## 输入文件

- `featureTable.biom` - ASV 丰度表（BIOM）
- `feature.fasta` - ASV 代表序列
- `group.list` - 样本分组（可选）
- `venng.list` - 功能维恩图分组列表（可选）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_funpre.sh" \
    -b "${AMPLICON_ROOT}/v2/examples/step4_funpre/featureTable.biom" \
    -s "${AMPLICON_ROOT}/v2/examples/step4_funpre/feature.fasta" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_funpre/group.list" \
    -v "${AMPLICON_ROOT}/v2/examples/step4_funpre/venng.list" \
    -o FunPre_Output/
```

## 示例来源

- 复制自：`/grj/BioAgent/test/ConstructASV/`、`group.list`

## 说明

- 仅适用于 **16S 细菌/古菌** PICRUSt2 功能预测；需相应软件与数据库环境。

## 输出

- `Visualization/`、`out_prediction/` 等
