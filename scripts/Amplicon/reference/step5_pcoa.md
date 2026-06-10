# PCoA - 主坐标分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | pcoa |
| **Description** | PCoA（Principal Co-ordinates Analysis）主坐标分析，基于 UniFrac 距离展示样本间的群落结构差异 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Beta 多样性排序分析 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| weighted_unifrac_pc.txt | Weighted UniFrac PCoA 坐标 | TSV | 16S | 细菌/古菌 | (${AMPLICON_ROOT}/examples/step5_pcoa/weighted_unifrac_pc.txt) |
| unweighted_unifrac_pc.txt | Unweighted UniFrac PCoA 坐标 | TSV | 16S | 细菌/古菌 | (${AMPLICON_ROOT}/examples/step5_pcoa/unweighted_unifrac_pc.txt) |
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step5_pcoa/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| PCoA.pdf | PCoA 合并排序图（PDF 格式） | PDF | 16S | 细菌/古菌 | - |
| PCoA.png | PCoA 合并排序图（PNG 格式） | PNG | 16S | 细菌/古菌 | - |
| weighted_unifrac/PCoA12.pdf | Weighted UniFrac PCoA 图 | PDF | 16S | 细菌/古菌 | - |
| weighted_unifrac/PCoA12.png | Weighted UniFrac PCoA 图 | PNG | 16S | 细菌/古菌 | - |
| unweighted_unifrac/PCoA12.pdf | Unweighted UniFrac PCoA 图 | PDF | 16S | 细菌/古菌 | - |
| unweighted_unifrac/PCoA12.png | Unweighted UniFrac PCoA 图 | PNG | 16S | 细菌/古菌 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step5_pcoa.sh -w weighted_unifrac_pc.txt -wu unweighted_unifrac_pc.txt -g group.list
# 输出：PCoA/PCoA.pdf, PCoA/weighted_unifrac/PCoA12.png 等
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step5_pcoa.sh -w weighted_unifrac_pc.txt -wu unweighted_unifrac_pc.txt -g group.list
# 输出：PCoA/PCoA.pdf, PCoA/PCoA.png, PCoA/weighted_unifrac/PCoA12.pdf 等
```

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -w, --weighted | Weighted UniFrac PCoA 坐标路径 | 是 | - | weighted_unifrac_pc.txt |
| -wu, --unweighted | Unweighted UniFrac PCoA 坐标路径 | 是 | - | unweighted_unifrac_pc.txt |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |

---

## 流程步骤

```
1️⃣ color_defined.pl（自动生成 group_col.list 分组颜色配置）
   ↓
2️⃣ plot_PCoA.R（绘制 Weighted UniFrac PCoA 图）
   ↓
3️⃣ plot_PCoA.R（绘制 Unweighted UniFrac PCoA 图）
   ↓
4️⃣ convert（合并两张 PCoA 图）
```

---

## group.list 格式

```
# 样本名\t分组名
Sample001\tGroupA
Sample002\tGroupA
Sample003\tGroupB
Sample004\tGroupB
```
---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **Rscript**: `/gfs/softwares/R/3.6.3/bin/Rscript`
- **convert**: `/usr/bin/convert` (ImageMagick)
- **perl**: `/usr/bin/perl`
- **plot_PCoA.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCoA/plot_PCoA.R`
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' > .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
echo 'export PERL_BIN="/your/path/to/perl"' >> .env
echo 'export PCOA_R_PL="/your/path/to/plot_PCoA.R"' >> .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step5_pcoa.sh ...
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| Beta 多样性计算 | weighted_unifrac_pc.txt, unweighted_unifrac_pc.txt | PCoA 坐标数据 |
| step3_table_stats | group.list | 样本分组信息 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | PCoA.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step5_pcoa.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step5_pcoa.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step5_pcoa/`

---

最后更新：2026-04-16
