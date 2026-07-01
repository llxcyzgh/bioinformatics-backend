# FLASH - 双端序列拼接模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | flash |
| **Description** | 快速重叠双端测序序列拼接工具，将配对的 R1 和 R2 reads 拼接成完整的扩增子序列 |
| **适用范围** | 16S/18S/ITS 扩增子测序、需要序列拼接的双端测序数据 |
| **估算机时** | 0.5 小时 |
| **报价分数** | 0.9 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| ${sample}_R1.fastq.gz | 正向测序文件 (双端) | FASTQ.GZ | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step1_flash/T1001_R1.fastq.gz) |
| ${sample}_R2.fastq.gz | 反向测序文件 (双端) | FASTQ.GZ | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step1_flash/T1001_R2.fastq.gz) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| ${sample}.out.extendedFrags.fastq | 成功拼接的序列 | FASTQ | 16S/18S/ITS | 通用 | - |
| ${sample}.notCombined_1.fastq | 未拼接的正向序列 | FASTQ | 16S/18S/ITS | 通用 | - |
| ${sample}.notCombined_2.fastq | 未拼接的反向序列 | FASTQ | 16S/18S/ITS | 通用 | - |
| ${sample}.flash.log | 拼接过程日志 | TXT | 通用 | 通用 | - |

---

## 执行命令

### 调用脚本 (推荐)

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step1_flash.sh -1 ${sample}_R1.fastq.gz -2 ${sample}_R2.fastq.gz -m <min_overlap> -M <max_overlap> -x <max_ratio> -o Flash_Output/
# 输出目录：Flash_Output/；文件：${sample}.out.extendedFrags.fastq, ${sample}.notCombined_1.fastq, ${sample}.notCombined_2.fastq, ${sample}.flash.log
```

**示例**（16S V3-V4）：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step1_flash.sh -1 T1001_R1.fastq.gz -2 T1001_R2.fastq.gz -m 10 -M 150 -x 0.1 -o Flash_Output/
# 输出目录：Flash_Output/；文件：CKM031.out.extendedFrags.fastq, CKM031.notCombined_1.fastq, CKM031.notCombined_2.fastq, CKM031.flash.log
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -1, --r1 | R1 测序文件路径 | 是 | - | T1001_R1.fastq.gz |
| -2, --r2 | R2 测序文件路径 | 是 | - | T1001_R2.fastq.gz |
| -m, --min-overlap | 最小重叠长度 | 否 | 10 | 10 |
| -M, --max-overlap | 最大重叠长度 | 否 | 250 | 150 |
| -x, --max-ratio | 最大错误率 | 否 | 0.1 | 0.1 |
| -t, --threads | 线程数 | 否 | 1 | 12 |
| -o, --output | 输出目录 | 是 | - | Flash_Output/ |

---

## 不同测序区域的推荐参数

| 测序区域 | 扩增子长度 | -m | -M | -x |
|----------|-----------|----|----|----|
| **16S V3-V4** | ~460bp | 10 | 150 | 0.1 |
| **16S V4** | ~250bp | 10 | 100 | 0.1 |
| **ITS1** | ~300bp | 10 | 120 | 0.1 |
| **ITS2** | ~350bp | 10 | 140 | 0.1 |

---

## 质量评估标准

| 指标 | 优秀 | 合格 | 不合格 |
|------|------|------|--------|
| **拼接率** | ≥90% | 70-90% | <70% |

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **flash**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/01.Split/lib/FLASH-1.2.7/flash`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export FLASH_BIN="/your/path/to/flash"' > .env
source .env
bash step1_flash.sh ... -o Flash_Output/
```

---
## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step1_flash.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step1_flash.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step1_flash/`

---

最后更新：2026-06-24
