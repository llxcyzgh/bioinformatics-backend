# 示例数据目录（`examples/`）

与 `reference/README.md` 中的 **`AMPLICON_ROOT`** 约定一致：本目录的规范路径为 **`${AMPLICON_ROOT}/examples/`**。

## 使用前

```bash
export AMPLICON_ROOT="/vol1/guorongjun/BioAgent/Amplicon/openclaw"   # 改为你的 clone 路径
```

## 说明

- 各 `step*/README.md` 中的 **`cd`**、**示例来源**、**测试命令** 已统一为 `${AMPLICON_ROOT}/examples/...` 与 `${AMPLICON_ROOT}/scripts/...`。
- **`step3_dada2/manifest.tsv`** 中 fastq 为 **绝对路径**（QIIME2 manifest 要求）。若你将仓库 clone 到其他位置，请用编辑器或脚本把第二列改为本机上的 `.../examples/step3_dada2/D1.fastq.gz`，或运行前在该目录生成 manifest。

## 子目录

每个 `step*` 子目录对应一类工具的极小示例，详见各目录内 `README.md`。
