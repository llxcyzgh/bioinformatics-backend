# Venn - 维恩图分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | venn |
| **Description** | 基于 ASV/OTU 丰度表绘制维恩图，展示不同样本或分组间的共有和特有物种分布 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组物种组成比较分析 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.group.even.txt | 分组均一化 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_venn/asv_table.group.even.txt) |
| asv_table.even.txt | 样本均一化 ASV 表（脚本内自动生成 asv_table.group.even.txt） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_venn/asv_table.even.txt) |
| group.list | 样本分组文件（-t 为 asv_table.even.txt 时必需） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_venn/group.list) |
| venn.G.list | 维恩图分组列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_venn/venn.G.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Venn_group/*.svg | 维恩图（SVG 格式） | SVG | 16S/18S/ITS | 通用 | - |
| Venn_group/*.png | 维恩图（PNG 格式） | PNG | 16S/18S/ITS | 通用 | - |
| Venn_group/*.xls | 维恩图数据表 | XLS | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_venn.sh -t asv_table.group.even.txt -l venn.G.list -o Venn_Output/
# 输出目录：Venn_Output/；文件：Venn_group/*.svg, Venn_group/*.png, Venn_group/*.xls
```

**示例 1**（分组均一化 ASV 表）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_venn.sh -t asv_table.group.even.txt -l venn.G.list -o Venn_Output/
```

**示例 2**（样本均一化 ASV 表，自动生成 asv_table.group.even.txt）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_venn.sh \
    -t TableStats/asv_table.even.txt \
    -g group.list \
    -l venn.G.list \
    -o Venn_Output/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -t, --table | 分组或样本均一化 ASV 表路径 | 是 | - | asv_table.group.even.txt |
| -g, --group | 样本分组文件（-t 为 asv_table.even.txt 时必需） | 条件必需 | - | group.list |
| -l, --list | 维恩图分组列表路径 | 是 | - | venn.G.list |
| -o, --output | 输出目录 | 是 | - | Venn_Output/ |

---

## venn.G.list 格式

```
# 空格分隔的分组名称（支持 2-5 个分组）
D DF Y Z
```

**说明**：
- 每行定义一组维恩图比较的分组
- 分组名称必须与 ASV 表中的分组名称一致
- 支持 2-5 个分组的维恩图

---

## 流程步骤

```
0️⃣（可选）combineTableFromSample2Group.pl 生成 asv_table.group.even.txt（-t 为 asv_table.even.txt 时）
   ↓
1️⃣ 读取分组 ASV 表和 venn.G.list
   ↓
2️⃣ venn.pl（计算共有和特有物种）
   ↓
3️⃣ 生成维恩图数据（*.xls）
   ↓
4️⃣ 绘制维恩图（*.svg）
   ↓
5️⃣ SVG → PNG 转换
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **combineTableFromSample2Group.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/combineTableFromSample2Group.pl`
- **venn.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/venn.pl`
- **convert**: `/usr/bin/convert` (ImageMagick)

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export COMBINE_SAMPLE2GROUP_PL="/your/path/to/combineTableFromSample2Group.pl"' >> .env
echo 'export VENN_PL="/your/path/to/venn.pl"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
source .env
bash step4_venn.sh ... -o Venn_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.group.even.txt、asv_table.even.txt | 分组/样本均一化 ASV 表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | Venn_group/*.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step4_venn.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step4_venn.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step4_venn/`

---

最后更新：2026-06-24
