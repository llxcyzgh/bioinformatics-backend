# step4_funpre 示例数据

## 输入文件

- `featureTable.biom` - ASV 丰度表（BIOM 格式，235B）
- `featureTable.tsv` - ASV 丰度表（TSV 格式，235B）
- `feature.fasta` - ASV 代表序列（8.3K, 20 条序列）
- `group.list` - 样本分组文件（196B, 20 个样本）
- `venng.list` - 功能维恩图分组列表（59B, 4 个分组）

## 测试命令

**BIOM 格式输入**：
```bash
cd "${AMPLICON_ROOT}/examples/step4_funpre"
bash "${AMPLICON_ROOT}/scripts/step4_funpre.sh" -b featureTable.biom -s feature.fasta -g group.list -v venng.list
```

**TSV 格式输入（自动转换）**：
```bash
bash "${AMPLICON_ROOT}/scripts/step4_funpre.sh" -b featureTable.tsv -s feature.fasta -g group.list -v venng.list
# 自动转换：featureTable.tsv → featureTable.biom
```

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step4_funpre/featureTable.biom`
- 输入：`${AMPLICON_ROOT}/examples/step4_funpre/feature.fasta`
- 输入：`${AMPLICON_ROOT}/examples/step4_funpre/group.list`
- 输出：`${AMPLICON_ROOT}/examples/step4_funpre/`（或由 `-o` 指定）
