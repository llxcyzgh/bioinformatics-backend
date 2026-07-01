# step4_randomforest 示例数据

## 输入文件

- `Relative/` - 各分类层级相对丰度表（8 个 `.xls`，**30 样本**：T100×15 + T200×15）
- `group.list` - 样本分组（T10001–T10015 → T100，T20001–T20015 → T200）
- `rf.list` - 对比组：`T100` vs `T200`（每组 **15** 个样本，满足脚本默认 `MIN_SAMPLES=15`）

## 说明

- 丰度表由 test 项目 12 样本中的 T100/T200 各 3 个样本**扩增**而来（循环复制 + 小幅扰动），专用于 Random Forest 示例，与 `step4_simper` 等模块的 12 样本示例相互独立。
- 若需降低门槛试跑，可设置 `export MIN_SAMPLES=3`（不推荐用于正式分析）。

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step4_randomforest.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step4_randomforest/Relative/" \
    -g "${AMPLICON_ROOT}/v2/examples/step4_randomforest/group.list" \
    -r "${AMPLICON_ROOT}/v2/examples/step4_randomforest/rf.list" \
    -l genus \
    -o RandomForest_Output/
```

## 示例来源

- 基础丰度：`/grj/BioAgent/test/TableStats/Relative/`（T1001–3、T2001–3 列）
- 扩增脚本：本地生成 15×2 样本列

## 输出

- `genus/impplot_*.png/pdf`、`genus/trainset_auc.png` 等
