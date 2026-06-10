# SIMPER - 相似性百分比分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | simper |
| **Description** | SIMPER（Similarity Percentage）分析，识别组间差异贡献最大的物种 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组差异物种筛选 |
| **估算机时** | 1.0 小时 |
| **报价分数** | 1.8 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative/ | 各分类层级相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_simper/Relative/) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_simper/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| */simper_*.txt | SIMPER 分析结果 | TXT | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_simper.sh -i Relative/ -g group.list
# 输出：*/simper_*.txt
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_simper.sh -i Relative/ -g group.list
# 输出：phylum/simper_*.txt, class/simper_*.txt, ...
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 相对丰度表目录路径 | 是 | - | Relative/ |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| --top | Top 物种数量 | 否 | 10 | 10 |

---

## 流程步骤

```
1️⃣ get.simper.pl（SIMPER 分析）
   ↓
2️⃣ 生成各层级 SIMPER 结果（simper_*.txt）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **get.simper.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/simper/get.simper.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export GET_SIMPER_PL="/your/path/to/get.simper.pl"' >> .env
source .env
bash step4_simper.sh ...
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
| 报告生成 | */simper_*.txt | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_simper.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_simper.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_simper/`

---

最后更新：2026-04-15
