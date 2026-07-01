# Network - 微生物网络分析模块

## 基本信息

| 字段 | 值 |
|------|-----|
| **Tool Name** | network |
| **Description** | 基于物种相对丰度构建微生物共现网络，识别物种间相互作用关系 |
| **适用范围** | 16S/18S/ITS 扩增子测序、微生物组网络分析 |
| **估算机时** | 3.0 小时 |
| **报价分数** | 5.4 |

---

## 输入

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| genus.relative.xls | 属水平相对丰度表 | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_network/genus.relative.xls) |
| group.list | 样本分组文件 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/v2/examples/step4_network/group.list) |

`group.list` 支持两种格式（制表符分隔）：

**两列**（样本ID \\t 组名）：
```
D1	D
Y.K1	Y
```

**三列及以上**（取最后一列为组名，常见于 Novogene 项目）：
```
SPN1.1	SPN1.1	SPN1
SPN14.1	SPN14.1	SPN14
```

脚本会自动提取所有唯一组名，对每组分别构建网络。

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| {group}/Shell/*.sh | 各组网络分析脚本 | SH | 16S/18S/ITS | 通用 | - |
| {group}/dot/igraph.calculate.txt | 各组网络计算结果 | TXT | 16S/18S/ITS | 通用 | - |
| {group}/dot/network.js | 各组网络交互数据 | JS | 16S/18S/ITS | 通用 | - |

每组对应 `group.list` 中的一个组名，输出子目录与组名一致（如 `D/`、`Y/`、`Z/`）。

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_network.sh -i genus.relative.xls -g group.list -o Network_Output/
# 输出目录：Network_Output/；文件：D/, Y/, Z/ 等（按 group.list 中的组名）
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/v2/scripts/step4_network.sh -i genus.relative.xls -g group.list -o Network_Output/
# 输出目录：Network_Output/；文件：D/Shell/, D/dot/, Y/Shell/, Y/dot/, Z/Shell/, Z/dot/ 等
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 属水平相对丰度表路径 | 是 | - | genus.relative.xls |
| -g, --group | 样本分组文件路径 | 是 | - | group.list |
| -o, --output | 输出目录 | 是 | - | Network_Output/ |

---

## 流程步骤

```
1️⃣ 从 group.list 提取所有组名，为每组生成样本列表
   ↓
2️⃣ derep.pl（去冗余处理）
   ↓
3️⃣ get_g_table.pl（生成 OTU 表）
   ↓
4️⃣ network.pipelinev2.pl（网络分析，生成 Shell 脚本）
   ↓
5️⃣ tab_js.pl（生成网络交互数据）
```

以上步骤对 `group.list` 中的每个组循环执行。

---

## 环境配置

### 默认路径

脚本内置默认软件路径，当前环境可直接使用：
- **perl**: `/usr/bin/perl`
- **derep.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/derep.pl`
- **get_g_table.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/NetWork/lib/get_g_table.pl`
- **network.pipelinev2.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/NetWork/bin/network.pipelinev2.pl`
- **tab_js.pl**: `/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/tab_js.pl`

### 自定义路径（迁移环境时）

如果软件路径不同，可通过环境变量覆盖：

**配置文件**
```bash
# 创建 .env 文件
echo 'export PERL_BIN="/your/path/to/perl"' > .env
echo 'export DEREP_PL="/your/path/to/derep.pl"' >> .env
echo 'export GET_G_TABLE_PL="/your/path/to/get_g_table.pl"' >> .env
echo 'export NETWORK_PIPELINE_PL="/your/path/to/network.pipelinev2.pl"' >> .env
echo 'export TAB_JS_PL="/your/path/to/tab_js.pl"' >> .env
source .env
bash step4_network.sh ... -o Network_Output/
```

---

## 上游工具

| 工具 | 输出文件 | 说明 |
|------|----------|------|
| step3_table_stats | Relative/genus.relative.xls | 属水平相对丰度表 |

---

## 下游工具

| 工具 | 输入文件 | 说明 |
|------|----------|------|
| 报告生成 | {group}/dot/network.js | 插入分析报告（交互式） |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/v2/scripts/step4_network.sh`
- **参考文档**: `${AMPLICON_ROOT}/v2/reference/step4_network.md`
- **示例数据**: `${AMPLICON_ROOT}/v2/examples/step4_network/`

---

最后更新：2026-06-24
