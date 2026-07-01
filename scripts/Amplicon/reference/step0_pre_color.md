# Pre Color - 分组颜色配置文件生成模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | pre_color |
| **Description** | 由 group.list 生成分组颜色配置文件 group_col.list，供下游可视化模块使用 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组可视化前置步骤 |
| **估算机时** | 0 小时 |
| **报价分数** | 0 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| group.list | 样本分组文件 | TSV | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step0_pre_color/group.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| group_col.list | 分组颜色配置（三列：样本 ID、分组名、颜色代码） | TSV | 16S/18S/ITS | 通用 | - |

> `-o` 可为输出文件路径（如 `group_col.list`）或输出目录下的文件名。

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step0_pre_color.sh -i group.list -o group_col.list
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step0_pre_color.sh \
    -i group.list \
    -o Color_Output/group_col.list
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --group | 样本分组文件路径 | 是 | - | group.list |
| -o, --output | 输出文件路径 | 是 | - | group_col.list |

---

## group.list 格式

```
# 样本名\t分组名
Sample001\tGroupA
Sample002\tGroupA
Sample003\tGroupB
```

---

## 流程步骤

```
1️⃣ color_defined.pl（读取 group.list，分配内置颜色表）
   ↓
2️⃣ 输出 group_col.list
```

---

## 环境配置

### 默认路径

- **perl**: `/usr/bin/perl`
- **color_defined.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl`

### 自定义路径

```bash
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export COLOR_DEFINED_PL="/your/path/to/color_defined.pl"' >> .env
source .env
bash step0_pre_color.sh -i group.list -o group_col.list
```

---

## 下游工具

多数 Step 4/5 可视化脚本会在内部自动调用 `color_defined.pl`；本模块用于需要**单独预生成**颜色配置的场景。

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| step5_pca / step5_pcoa / step5_nmds 等 | group_col.list | 分组着色（多数脚本可自动生成，无需单独运行本步） |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step0_pre_color.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step0_pre_color.md`

---

最后更新：2026-06-24
