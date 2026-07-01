# Beta Data - Beta 多样性分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | beta_data |
| **Description** | Beta 多样性分析，计算样本间差异，生成 PCoA 排序图和 Emperor 交互式可视化 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组群落结构比较分析 |
| **估算机时** | 1.0 小时 |
| **报价分数** | 1.8 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| asv_table.even.txt | 均一化 ASV 表 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_beta_data/asv_table.even.txt) |
| rooted-tree.qza | 有根系统发育树 | QZA | 16S/18S/ITS | 通用 | - |
| alpha.mf | 样本元数据文件（表头：`#SampleID	Description`） | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step3_alpha_data/alpha.mf) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| rarefied_table.qza | 重采样后的 ASV 表 | QZA | 16S/18S/ITS | 通用 | - |
| asv_table.even.qza | QIIME2 特征表（由 TSV 转换生成） | QZA | 16S/18S/ITS | 通用 | - |
| metadata.qiime.mf | 补全表头后的元数据（仅当输入缺少表头时生成） | TSV | 16S/18S/ITS | 通用 | - |
| faith_pd_vector.qza | Faith 系统发育多样性指数 | QZA | 16S/18S/ITS | 通用 | - |
| observed_features_vector.qza | 观测物种数向量 | QZA | 16S/18S/ITS | 通用 | - |
| shannon_vector.qza | Shannon 多样性指数向量 | QZA | 16S/18S/ITS | 通用 | - |
| evenness_vector.qza | Pielou 均匀度向量 | QZA | 16S/18S/ITS | 通用 | - |
| unweighted_unifrac_distance_matrix.qza | 非加权 UniFrac 距离矩阵 | QZA | 16S/18S/ITS | 通用 | - |
| weighted_unifrac_distance_matrix.qza | 加权 UniFrac 距离矩阵 | QZA | 16S/18S/ITS | 通用 | - |
| jaccard_distance_matrix.qza | Jaccard 距离矩阵 | QZA | 16S/18S/ITS | 通用 | - |
| bray_curtis_distance_matrix.qza | Bray-Curtis 距离矩阵 | QZA | 16S/18S/ITS | 通用 | - |
| unweighted_unifrac_pcoa_results.qza | 非加权 UniFrac PCoA 结果 | QZA | 16S/18S/ITS | 通用 | - |
| weighted_unifrac_pcoa_results.qza | 加权 UniFrac PCoA 结果 | QZA | 16S/18S/ITS | 通用 | - |
| jaccard_pcoa_results.qza | Jaccard PCoA 结果 | QZA | 16S/18S/ITS | 通用 | - |
| bray_curtis_pcoa_results.qza | Bray-Curtis PCoA 结果 | QZA | 16S/18S/ITS | 通用 | - |
| unweighted_unifrac_emperor.qzv | 非加权 UniFrac Emperor 可视化 | QZV | 16S/18S/ITS | 通用 | - |
| weighted_unifrac_emperor.qzv | 加权 UniFrac Emperor 可视化 | QZV | 16S/18S/ITS | 通用 | - |
| jaccard_emperor.qzv | Jaccard Emperor 可视化 | QZV | 16S/18S/ITS | 通用 | - |
| bray_curtis_emperor.qzv | Bray-Curtis Emperor 可视化 | QZV | 16S/18S/ITS | 通用 | - |
| *_qza/ | QZA 解压目录（距离矩阵、PCoA 坐标等） | 目录 | 16S/18S/ITS | 通用 | - |
| *_qzv/ | QZV 解压目录（Emperor 可视化数据） | 目录 | 16S/18S/ITS | 通用 | - |
| unweighted_unifrac_pcoa_results_qza/ordination.txt | 非加权 UniFrac PCoA 坐标 | TXT | 16S/18S/ITS | 通用 | - |
| weighted_unifrac_pcoa_results_qza/ordination.txt | 加权 UniFrac PCoA 坐标 | TXT | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_beta_data.sh -i asv_table.even.txt -t rooted-tree.qza -m alpha.mf -o BetaData_Output/
# 输出目录：BetaData_Output/；文件：asv_table.even.qza, *_distance_matrix.qza, *_pcoa_results.qza, *_emperor.qzv
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step3_beta_data.sh -i asv_table.even.txt -t rooted-tree.qza -m alpha.mf -o BetaData_Output/
# 输出目录：BetaData_Output/；文件：asv_table.even.qza, rarefied_table.qza, faith_pd_vector.qza, ..., bray_curtis_emperor.qzv
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 均一化 ASV 表路径（TSV/TXT，也支持 QZA） | 是 | - | asv_table.even.txt |
| -t, --tree | 有根系统发育树路径 | 是 | - | rooted-tree.qza |
| -m, --meta | 样本元数据文件路径（需含 `#SampleID	Description` 表头，缺失时自动补全） | 是 | - | alpha.mf |
| -o, --output | 输出目录 | 是 | - | BetaData_Output/ |
| -d, --depth | 采样深度 | 否 | 自动取最小样本 reads 数 | 5000 |

### 元数据格式（alpha.mf）

QIIME2 要求元数据首行为 `#SampleID	Description`（Tab 分隔）。脚本会自动检测：若缺少该表头，会在输出目录生成 `metadata.qiime.mf` 并补全表头后再分析。

```
#SampleID	Description
D1	D
D2	D
Y.K1	Y
...
```

---

## Beta 多样性距离算法

| 距离算法 | 是否考虑进化关系 | 是否考虑丰度 | 说明 |
|----------|------------------|--------------|------|
| **Unweighted UniFrac** | ✅ 是 | ❌ 否 | 基于进化关系的定性距离 |
| **Weighted UniFrac** | ✅ 是 | ✅ 是 | 基于进化关系的定量距离 |
| **Jaccard** | ❌ 否 | ❌ 否 | 基于物种有无的定性距离 |
| **Bray-Curtis** | ❌ 否 | ✅ 是 | 基于物种丰度的定量距离 |

---

## 流程步骤

```
1️⃣ TSV → BIOM 转换（biom convert）
   ↓
2️⃣ BIOM → QZA 导入（qiime tools import）
   ↓
3️⃣ 自动计算采样深度（最小样本 reads 数）
   ↓
4️⃣ core-metrics-phylogenetic（核心多样性分析）
   ↓
5️⃣ qiime tools export（导出所有 QZA/QZV 解压结果）
   ↓
6️⃣ 输出 *_qza/（距离矩阵、PCoA ordination.txt 等）和 *_qzv/（Emperor 数据）
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
bash step3_beta_data.sh ... -o BetaData_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | asv_table.even.txt | 均一化 ASV 表 |
| step3_phylogeny | rooted-tree.qza | 有根系统发育树 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step3_upgma | *_pcoa_results_qza/ordination.txt | UPGMA / PCoA 坐标整理（pcoa.pl） |
| step5_pcoa | BetaData/*_pcoa_results_qza/ordination.txt | PCoA 排序图（`-i` + `-d` 选距离） |
| step5_beta_div | *_distance_matrix_qza/ | Beta 多样性组间差异检验 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step3_beta_data.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step3_beta_data.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step3_beta_data/`

---

最后更新：2026-06-24
