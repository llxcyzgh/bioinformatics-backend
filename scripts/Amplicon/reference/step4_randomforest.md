# Random Forest - 随机森林分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | random_forest |
| **Description** | 随机森林分析，识别组间差异物种并评估分类性能（AUC 曲线） |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组生物标志物筛选 |
| **估算机时** | 2.5 小时 |
| **报价分数** | 4.5 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative/ | 各分类层级相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_randomforest/Relative/) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_randomforest/group.list) |
| rf.list | Random Forest 对比列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_randomforest/rf.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| */impplot_MeanDecreaseAccuracy*.png/pdf | 重要性图（准确率） | PNG/PDF | 16S/18S/ITS | 通用 | - |
| */impplot_MeanDecreaseGini*.png/pdf | 重要性图（基尼系数） | PNG/PDF | 16S/18S/ITS | 通用 | - |
| */trainset_auc.png/pdf | 训练集 AUC 曲线 | PNG/PDF | 16S/18S/ITS | 通用 | - |
| */testset_auc.png/pdf | 测试集 AUC 曲线 | PNG/PDF | 16S/18S/ITS | 通用 | - |
| tax_show_ea.png/pdf | 重要性图合并图 | PNG/PDF | 16S/18S/ITS | 通用 | - |
| auc.png/pdf | AUC 曲线合并图 | PNG/PDF | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_randomforest.sh -i Relative/ -g group.list -r rf.list
# 输出：*/impplot_*, */auc.png, tax_show_ea.png, auc.png
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_randomforest.sh -i Relative/ -g group.list -r rf.list
# 输出：genus/impplot_*, genus/auc.png, tax_show_ea.png, auc.png
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --indir | 相对丰度表目录路径 | 是 | - | Relative/ |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -r, --rf-list | Random Forest 对比列表路径 | 是 | - | rf.list |

---

## rf.list 格式

```
# Random Forest 对比列表
# 格式：Group1<TAB>Group2（制表符分隔）
D	DF
Y	Z
```

**说明**：
- 每行定义一组对比，使用**制表符（Tab）分隔**两个组名
- 第一列为 Group1，第二列为 Group2
- 分组名称必须与 `group.list` 中的分组名称一致
- 支持多组对比，每行一组

---

## 流程步骤

```
1️⃣ rf_roc.pl（随机森林 + ROC 曲线分析）
   ↓
2️⃣ 生成重要性图（MeanDecreaseAccuracy, MeanDecreaseGini）
   ↓
3️⃣ 生成 AUC 曲线（trainset, testset）
   ↓
4️⃣ 合并图片（tax_show_ea.png, auc.png）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **rf_roc.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/rf_roc/rf_roc.pl`
- **convert**: `/usr/bin/convert` (ImageMagick)

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export RF_ROC_PL="/your/path/to/rf_roc.pl"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
source .env
bash step4_randomforest.sh ...
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
| 报告生成 | tax_show_ea.png | 插入分析报告 |
| 报告生成 | auc.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_randomforest.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_randomforest.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_randomforest/`

---

最后更新：2026-04-15
