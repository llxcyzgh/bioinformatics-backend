# Ternary Plot - 三元相图分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | ternary |
| **Description** | 三元相图分析，可视化展示三个分组间的物种组成分布 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组三组比较分析 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Relative_group/ | 分组相对丰度表目录 | DIR | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_ternary/Relative_group/) |
| ternary.list | 三元相图分组列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_ternary/ternary.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| *.svg | 三元相图（SVG 格式） | SVG | 16S/18S/ITS | 通用 | - |
| *.png | 三元相图（PNG 格式） | PNG | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_ternary.sh -i Relative_group/ -l ternary.list
# 输出：*.svg, *.png
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_ternary.sh -i Relative_group/ -l ternary.list
# 输出：D_DF_Y.svg, D_DF_Y.png, Y_Z_D.svg, Y_Z_D.png
```
### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 分组相对丰度表目录路径 | 是 | - | Relative_group/ |
| -l, --list | 三元相图分组列表路径 | 是 | - | ternary.list |

---

## ternary.list 格式

```
# 三元相图分组列表
# 格式：Group1_Group2_Group3
D_DF_Y
Y_Z_D
```

**说明**：
- 每行定义一组三元对比（Group1_Group2_Group3）
- 分组名称必须与 `Relative_group/` 中的分组名称一致
- 支持多组三元对比

---

## 流程步骤

```
1️⃣ ternaryplot.pl（三元相图绘制）
   ↓
2️⃣ 生成 SVG 格式三元图
   ↓
3️⃣ SVG → PNG 转换
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **ternaryplot.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/ternaryplot.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export TERNARYPLOT_PL="/your/path/to/ternaryplot.pl"' >> .env
source .env
bash step4_ternary.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative_group/ | 分组相对丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | *.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_ternary.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_ternary.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_ternary/`

---

最后更新：2026-04-15
