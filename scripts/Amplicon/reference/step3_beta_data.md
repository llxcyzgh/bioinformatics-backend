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
| asv_table.even.qza | 均一化 ASV 表（QIIME2） | QZA | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_beta_data/asv_table.even.txt) |
| rooted-tree.qza | 有根系统发育树 | QZA | 16S/18S/ITS | 通用 | - |
| alpha.mf | 样本元数据文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step3_beta_data/alpha.mf) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| rarefied_table.qza | 重采样后的 ASV 表 | QZA | 16S/18S/ITS | 通用 | - |
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

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_beta_data.sh -i asv_table.even.qza -t rooted-tree.qza -m alpha.mf
# 输出：*_distance_matrix.qza, *_pcoa_results.qza, *_emperor.qzv
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step3_beta_data.sh -i asv_table.even.qza -t rooted-tree.qza -m alpha.mf
# 输出：rarefied_table.qza, faith_pd_vector.qza, ..., bray_curtis_emperor.qzv
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 均一化 ASV 表路径 | 是 | - | asv_table.even.qza |
| -t, --tree | 有根系统发育树路径 | 是 | - | rooted-tree.qza |
| -m, --meta | 样本元数据文件路径 | 是 | - | alpha.mf |

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
1️⃣ 导入 QIIME2 环境
   ↓
2️⃣ core-metrics-phylogenetic（核心多样性分析）
   ↓
3️⃣ 计算 4 种距离矩阵（UniFrac, Jaccard, Bray-Curtis）
   ↓
4️⃣ PCoA 降维排序
   ↓
5️⃣ 生成 Emperor 交互式可视化
   ↓
6️⃣ 导出所有 qza/qzv 文件
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
bash step3_beta_data.sh ...
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
| step4_beta | *_distance_matrix.qza | Beta 多样性统计检验 |
| step4_pcoa | *_pcoa_results.qza | PCoA 排序图 |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step3_beta_data.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step3_beta_data.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step3_beta_data/`

---

最后更新：2026-04-15
