# Phylogeny - 系统发育树构建模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | phylogeny |
| **Description** | 基于 ASV 代表序列构建系统发育树，用于 Beta 多样性分析和进化关系研究 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组系统发育分析 |
| **估算机时** | 3.0 小时 |
| **报价分数** | 5.4 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|------|
| featureSeqs.qza | ASV 代表序列（QIIME2） | QZA | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_phylogeny/featureSeqs.qza) |
| sequences.fasta | ASV 代表序列（FASTA） | FASTA | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_phylogeny/sequences.fasta) |

**自动格式检测**：
- 脚本自动检测输入文件格式（`.qza` 或 `.fasta/.fa/.fna`）
- 如果是 FASTA 格式，自动转换为 QIIME2 qza 格式
- 转换过程透明，完成后自动清理临时文件

---

## 输出

> 所有输出文件均写入 `-o` 指定的目录（下表路径相对于输出目录）。

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Phylogeny_Output/rooted-tree.qza | 有根系统发育树（QIIME2） | QZA | 16S/18S/ITS | 通用 | - |
| Phylogeny_Output/unrooted-tree.qza | 无根系统发育树（QIIME2） | QZA | 16S/18S/ITS | 通用 | - |
| Phylogeny_Output/rooted_tree.nwk | 有根系统发育树（Newick） | NWK | 16S/18S/ITS | 通用 | - |
| Phylogeny_Output/unrooted_tree.nwk | 无根系统发育树（Newick） | NWK | 16S/18S/ITS | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_phylogeny.sh -i <输入文件> -n <threads> -o Phylogeny_Output/
# 输出目录：Phylogeny_Output/；文件：rooted-tree.qza, unrooted-tree.qza, rooted_tree.nwk, unrooted_tree.nwk
```

**示例 1**：使用 step3_dada2 输出（qza 格式）
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_phylogeny.sh -i featureSeqs.qza -n 12 -o Phylogeny_Output/
# 输出目录：Phylogeny_Output/；文件：rooted-tree.qza, unrooted-tree.qza, rooted_tree.nwk, unrooted_tree.nwk
```

**示例 2**：使用用户提供的 FASTA 文件
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_phylogeny.sh -i ASV_representative_sequences.fasta -n 12 -o Phylogeny_Output/
# 自动转换：ASV_representative_sequences.fasta → featureSeqs_temp.qza
# 输出目录：Phylogeny_Output/；文件：rooted-tree.qza, unrooted-tree.qza, rooted_tree.nwk, unrooted_tree.nwk
```

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 输入文件路径（.qza 或 .fasta/.fa/.fna） | 是 | - | featureSeqs.qza 或 sequences.fasta |
| -n, --threads | 线程数 | 否 | 12 | 12 |
| -o, --output | 输出目录 | 是 | - | Phylogeny_Output/ |

---

## 流程步骤

```
1️⃣ 检测输入格式（.qza 或 .fasta）
   ↓
2️⃣ FASTA? → 转换为 qza（自动）
   ↓
3️⃣ 多序列比对（mafft）
   ↓
4️⃣ 构建进化树（fasttree）
   ↓
5️⃣ 导出 Newick 格式
   ↓
6️⃣ 清理临时文件（如果是转换的）
```
---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **conda**: `/software/anaconda3/bin/conda`
- **qiime**: `/software/anaconda3/envs/16s-env/bin/qiime`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export CONDA_BIN="/your/path/to/conda"' > .env
echo 'export QIIME_BIN="/your/path/to/qiime"' >> .env
source .env
bash step3_phylogeny.sh ... -o Phylogeny_Output/
```
---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_dada2 | featureSeqs.qza | ASV 代表序列 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step5_beta | rooted-tree.qza | Beta 多样性分析（UniFrac） |
| step5_phylo_diversity | rooted-tree.qza | 系统发育多样性分析 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step3_phylogeny.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step3_phylogeny.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step3_phylogeny/`

---

最后更新：2026-06-24
