# step4_lefse 示例数据

## 输入文件

- `Relative/` - 各分类层级相对丰度表目录（7 个文件，84K）
- `all.mf` - 样本元数据文件（212B, 20 个样本）
- `lefse_vs.list` - LEfSe 对比分组列表（64B, 2 组对比）

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step4_lefse"
bash "${AMPLICON_ROOT}/scripts/step4_lefse.sh" -i Relative/ -m all.mf -v lefse_vs.list
```

## 示例来源

- 输入：`${AMPLICON_ROOT}/examples/step4_lefse/Relative/`
- 输入：`${AMPLICON_ROOT}/examples/step4_lefse/all.mf`
- 输入：`${AMPLICON_ROOT}/examples/step4_lefse/lefse_vs.list`
- 输出：`${AMPLICON_ROOT}/examples/step4_lefse/`（或由 `-o` 指定）
