# Network3D - 3D 微生物网络可视化模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | network3d |
| **Description** | 基于物种相对丰度构建 3D 微生物网络，可视化展示物种间相互作用关系 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 3D 网络可视化 |
| **估算机时** | 2.0 小时 |
| **报价分数** | 3.6 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| genus.relative.xls | 属水平相对丰度表 | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_network3d/genus.relative.xls) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| map.txt | 物种映射文件 | TXT | 16S/18S/ITS | 通用 | - |
| edgeplot.xls | 边数据文件 | XLS | 16S/18S/ITS | 通用 | - |
| node.xls | 节点数据文件 | XLS | 16S/18S/ITS | 通用 | - |
| network3D.html | 3D 网络可视化（如果生成） | HTML | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_network3d.sh -i genus.relative.xls -o Network3D_Output/
# 输出目录：Network3D_Output/；文件：map.txt, edgeplot.xls, node.xls
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_network3d.sh -i genus.relative.xls -o Network3D_Output/
# 输出目录：Network3D_Output/；文件：map.txt, edgeplot.xls, node.xls, network3D.html
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 属水平相对丰度表路径 | 是 | - | genus.relative.xls |
| -n, --top-n | Top 物种数量 | 否 | 100 | 100 |
| -o, --output | 输出目录 | 是 | - | Network3D_Output/ |

---

## 流程步骤

```
1️⃣ derep.pl（去冗余处理）
   ↓
2️⃣ map.pl（生成物种映射）
   ↓
3️⃣ net_file_generate.R（生成网络文件）
   ↓
4️⃣ Bayes_net_plot.R（绘制 3D 网络）
```

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **derep.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/derep.pl`
- **map.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/map.pl`
- **Rscript**: `/gfs/softwares/R/3.6.3/bin/Rscript`
- **net_file_generate.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/net_file_generate.R`
- **Bayes_net_plot.R**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/Bayes_net_plot.R`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export DEREP_PL="/your/path/to/derep.pl"' >> .env
echo 'export MAP_PL="/your/path/to/map.pl"' >> .env
echo 'export RSCRIPT_BIN="/your/path/to/Rscript"' >> .env
echo 'export NET_FILE_GENERATE_R="/your/path/to/net_file_generate.R"' >> .env
echo 'export BAYES_NET_PLOT_R="/your/path/to/Bayes_net_plot.R"' >> .env
source .env
bash step4_network3d.sh ... -o Network3D_Output/
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
| 报告生成 | network3D.html | 插入分析报告（3D 交互式） |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step4_network3d.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step4_network3d.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step4_network3d/`

---

最后更新：2026-06-24
