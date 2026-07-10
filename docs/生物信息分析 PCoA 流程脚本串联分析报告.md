# 生物信息分析 PCoA 流程脚本串联分析报告

## 一、 分析概述

本报告针对用户提供的 PCoA 编排脚本（主脚本）及其调用的 10 个节点脚本（`step1_cutadapt.sh` 至 `step5_pcoa.sh`）进行了详细的输入输出逻辑审计。核心目的是检查主脚本在串联各节点时，是否存在因硬编码路径、参数传递错误或文件名不匹配导致的流程中断问题。

经过对所有底层 `.sh` 源码的深度解析，发现主编排脚本在 **引物参数传递**、**输入路径硬编码**、**文件类型不匹配** 以及 **缺失必需输入文件** 等多个环节存在严重问题。各节点内部由于采用了统一的绝对路径转换机制（`abs_path.sh`），并未因相对路径导致目录切换失效，但主脚本的调用方式与节点实际的输入期望存在显著偏差。

## 二、 核心问题诊断

### 1. Step 1 (Cutadapt): 引物参数缺失导致流程阻断
- **问题描述**：主脚本在调用 `step1_cutadapt.sh` 时，传入了空的引物参数：`-f ""` 和 `-r ""`。
- **源码分析**：在 `step1_cutadapt.sh` 的第 58-59 行存在严格的非空校验逻辑：
  ```bash
  [ -z "${F_PRIMER}" ] && { echo "❌ 错误：必须提供 -f"; exit 1; }
  [ -z "${R_PRIMER}" ] && { echo "❌ 错误：必须提供 -r"; exit 1; }
  ```
- **影响**：由于参数为空，该节点会直接报错并退出，导致整个后续流程无法执行。

### 2. Step 4 (DADA2): 节点源码存在相对路径硬编码
- **问题描述**：`step3_dada2.sh` 脚本在执行 QIIME2 导入后，去噪步骤存在硬编码的相对路径，且与主脚本生成的 manifest 文件路径存在冲突。
- **源码分析**：在 `step3_dada2.sh` 的第 99-100 行：
  ```bash
  qiime dada2 denoise-single \
     --i-demultiplexed-seqs ../allFastq.qza \
  ```
  脚本在第 86 行切换到了输出目录 `cd "${PROJECT_DIR}"`，并在第 91-95 行将数据导入为 `allFastq.qza`（保存在当前输出目录下）。然而，在执行 `denoise-single` 时，脚本错误地引用了 `../allFastq.qza`，这会导致 QIIME2 找不到输入文件。
- **影响**：DADA2 去噪步骤将因找不到 `allFastq.qza` 而失败。

### 3. Step 8 (Table Stats): 缺失分组参数导致未生成下游所需的分组文件
- **问题描述**：主脚本在调用 `step3_table_stats.sh` 时未提供 `-g`（分组文件）参数。
- **源码分析**：根据 `step3_table_stats.sh` 的实现，仅在提供 `-g` 参数时，才会执行生成分组相关的均一化表和相对丰度表：
  ```bash
  if [ -n "${GROUP_LIST}" ]; then
      # 生成 asv_table.group.even.txt 等
  fi
  ```
- **影响**：虽然这一步未报错，但不会生成下游分析可能依赖的分组统计结果。更关键的是，主脚本在后续步骤中也没有统一的分组文件传递逻辑。

### 4. Step 10 (PCoA): 输入文件类型不匹配与不存在的 `group.list`
- **问题描述**：主脚本在调用 `step5_pcoa.sh` 时，传入的参数存在严重错误。
  ```bash
  bash ${AMPLICON_ROOT}/Amplicon/scripts/step5_pcoa.sh \
    -w "BetaData_Output/bray_curtis_pcoa_results.qza" \
    -wu "BetaData_Output/bray_curtis_pcoa_results.qza" \
    -g group.list \
    -o "PCoA_Output"
  ```
- **源码分析**：
  1. **输入类型错误**：`step5_pcoa.sh` 的 `-w` 和 `-wu` 参数设计用于接收旧版的 `*_pc.txt` 坐标文件，而不是 QIIME2 的 `.qza` 格式文件。若要使用 Beta 多样性的输出，应使用 `-i "BetaData_Output"` 传递整个目录，脚本会自动寻找 `ordination.txt`。
  2. **缺失的分组文件**：主脚本传递了 `-g group.list`，但在此前的任何步骤中均未生成名为 `group.list` 的文件（Step 9 传入的是 `.csv` 元数据文件）。`step5_pcoa.sh` 在第 152 行会检查该文件是否存在，若不存在则报错退出。
- **影响**：PCoA 分析将直接报错退出。

## 三、 修正方案与建议

为了使整个编排脚本能够顺畅运行，需对主脚本及部分节点源码进行如下修改：

### 1. 修正主编排脚本
- **Step 1**：为 Cutadapt 提供实际的引物序列，或在不需要去引物时跳过此步骤。
  ```bash
  -f "ACTG..." -r "TGCA..."
  ```
- **Step 8**：如果下游需要分组统计，需传入正确的分组文件。
- **Step 10**：修正 PCoA 的调用方式，使用 `-i` 传递 BetaData 目录，并确保提供正确格式的 TSV 分组文件（而不是 CSV 元数据）。
  ```bash
  bash ${AMPLICON_ROOT}/Amplicon/scripts/step5_pcoa.sh \
    -i "BetaData_Output" \
    -g "group.list" \
    -o "PCoA_Output"
  ```
  *(注：需要在脚本前期从 `METADATA` 中提取或生成 `group.list` 文件)*

### 2. 修正节点源码
- **`step3_dada2.sh`**：修改第 100 行，将 `../allFastq.qza` 修正为当前目录下的 `allFastq.qza`。
  ```bash
  # 原代码
  --i-demultiplexed-seqs ../allFastq.qza \
  # 修正为
  --i-demultiplexed-seqs allFastq.qza \
  ```

## 四、 总结
当前主编排脚本未能准确串联起 10 个节点的输入和输出。主要阻断点在于：引物参数为空、DADA2 节点内部的相对路径硬编码错误，以及 PCoA 节点接收了错误的文件类型并引用了不存在的分组文件。按照上述修正方案进行调整后，方可实现端到端的自动化运行。
