# Krona - 交互式物种组成可视化模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | krona |
| **Description** | Krona 交互式层级图表，可视化展示样本物种组成和丰度分布 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组物种组成可视化 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化 ASV 表（含分类学信息） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_krona/asv_table.even.txt) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| krona.html | Krona 交互式图表 | HTML | 16S/18S/ITS | 通用 | - |
| img/ | Krona 图片资源 | DIR | 16S/18S/ITS | 通用 | - |
| src/ | Krona JavaScript 源码 | DIR | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_krona.sh -t asv_table.even.txt
# 输出：krona.html, img/, src/
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_krona.sh -t asv_table.even.txt
# 输出：krona.html, img/, src/
```
### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -t, --table | 均一化 ASV 表路径 | 是 | - | asv_table.even.txt |
| -o, --output | 输出目录名称 | 否 | krona | krona |

---

## 流程步骤

```
1️⃣ ImportRDP.pl（解析 ASV 表和分类学信息）
   ↓
2️⃣ 生成 krona.html（交互式图表）
   ↓
3️⃣ 复制资源文件（img/, src/）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **ImportRDP.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Krona/ImportRDP.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export IMPORT_RDP_PL="/your/path/to/ImportRDP.pl"' >> .env
source .env
bash step4_krona.sh ...
```
---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt | 均一化 ASV 表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | krona.html | 插入分析报告（交互式） |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_krona.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_krona.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_krona/`

---

最后更新：2026-04-15
