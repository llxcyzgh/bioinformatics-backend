# UPGMA - 基于 UniFrac 距离的系统发育树模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | upgma |
| **Description** | 基于 Unweighted/Weighted UniFrac 距离矩阵构建 UPGMA 系统发育树，展示样本间的系统发育关系 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组 Beta 多样性分析 |
| **估算机时** | 1.5 小时 |
| **报价分数** | 2.7 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_upgma/asv_table.even.txt) |
| rooted-tree.nwk | 有根系统发育树 | NWK | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_upgma/rooted-tree.nwk) |
| alpha.mf | 样本元数据文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_upgma/alpha.mf) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| UPGMA_sample/unweighted_unifrac.png | 样本 Unweighted 树 | PNG | 16S/18S/ITS | 通用 | - |
| UPGMA_sample/weighted_unifrac.png | 样本 Weighted 树 | PNG | 16S/18S/ITS | 通用 | - |
| UPGMA_group/unweighted_unifrac.png | 分组 Unweighted 树 | PNG | 16S/18S/ITS | 通用 | - |
| UPGMA_group/weighted_unifrac.png | 分组 Weighted 树 | PNG | 16S/18S/ITS | 通用 | - |
| PCoA_data/*_dm.txt | 距离矩阵 | TXT | 16S/18S/ITS | 通用 | - |
| PCoA_data/*_pc.txt | PCoA 坐标 | TXT | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_upgma.sh -i asv_table.even.txt -t rooted-tree.nwk -m alpha.mf
# 输出：UPGMA_sample/*.png, UPGMA_group/*.png, PCoA_data/*.txt
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_upgma.sh -i asv_table.even.txt -t rooted-tree.nwk -m alpha.mf
# 输出：UPGMA_sample/unweighted_unifrac.png, UPGMA_sample/weighted_unifrac.png, ...
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 均一化 ASV 表路径 | 是 | - | asv_table.even.txt |
| -t, --tree | 有根系统发育树路径 | 是 | - | rooted-tree.nwk |
| -m, --meta | 样本元数据文件路径 | 是 | - | alpha.mf |

---

## 流程步骤

```
1️⃣ 激活 QIIME1 环境
   ↓
2️⃣ jackknifed_beta_diversity.py（样本 UPGMA 树构建）
   ↓
3️⃣ make_bootstrapped_tree.py（添加 bootstrap 支持值）
   ↓
4️⃣ SVG → PNG 转换（convert）
   ↓
5️⃣ 分组 UPGMA 树构建（同上流程）
   ↓
6️⃣ 距离矩阵和 PCoA 坐标整理
```

---

## UPGMA 树类型

| 树类型 | 距离算法 | 是否考虑丰度 | 说明 |
|--------|---------|-------------|------|
| **Unweighted UniFrac** | 非加权 | ❌ 否 | 基于进化关系的定性距离 |
| **Weighted UniFrac** | 加权 | ✅ 是 | 基于进化关系的定量距离 |

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **conda**: `/gfs/users/guorongjun/miniconda3/bin/conda`
- **qiime1**: QIIME1 环境
- **jackknifed_beta_diversity.py**: QIIME1 脚本
- **make_bootstrapped_tree.py**: QIIME1 脚本
- **convert**: `/usr/bin/convert` (ImageMagick)

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CONDA_BIN="/your/path/to/conda"' > .env
echo 'export QIIME1_ENV="/your/path/to/qiime1"' >> .env
echo 'export CONVERT_BIN="/your/path/to/convert"' >> .env
source .env
bash step3_upgma.sh ...
```
---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt | 均一化 ASV 表 |
| step3_phylogeny | rooted-tree.nwk | 有根系统发育树 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step4_beta | PCoA_data/*_dm.txt | Beta 多样性统计检验 |
| 报告生成 | UPGMA_sample/*.png | 插入分析报告 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step3_upgma.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step3_upgma.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step3_upgma/`

---

最后更新：2026-04-15
