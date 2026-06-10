# T-Test - T 检验与 Wilcoxon 检验模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | ttest |
| **Description** | T 检验和 Wilcoxon 秩和检验，识别组间具有显著差异的物种 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组差异物种筛选 |
| **估算机时** | 1.0 小时 |
| **报价分数** | 1.8 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative/ | 各分类层级相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_ttest/Relative/) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_ttest/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| */t_test_*.txt | T 检验结果 | TXT | 16S/18S/ITS | 通用 | - |
| */wilcox_test_*.txt | Wilcoxon 检验结果 | TXT | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_ttest.sh -i Relative/ -g group.list [--threshold <P 值>]
# 输出：*/t_test_*.txt, */wilcox_test_*.txt
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_ttest.sh -i Relative/ -g group.list --threshold 0.05
# 输出：phylum/t_test_*.txt, phylum/wilcox_test_*.txt, ...
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 相对丰度表目录路径 | 是 | - | Relative/ |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| --threshold | P 值阈值 | 否 | 0.05 | 0.05 |
| --method | 检验方法 | 否 | t | t 或 wilcox |

---

## 流程步骤

```
1️⃣ get.t.wilcox.pl（T 检验和 Wilcoxon 检验）
   ↓
2️⃣ 生成各层级检验结果（t_test_*.txt, wilcox_test_*.txt）
```
---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **get.t.wilcox.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/t.wilcox.R.lib/get.t.wilcox.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export GET_T_WILCOX_PL="/your/path/to/get.t.wilcox.pl"' >> .env
source .env
bash step4_ttest.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative/ | 各分类层级相对丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | */t_test_*.txt | 插入分析报告 |
| 报告生成 | */wilcox_test_*.txt | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_ttest.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_ttest.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_ttest/`

---

最后更新：2026-04-15
