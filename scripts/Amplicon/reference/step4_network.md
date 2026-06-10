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
| genus.relative.xls | 属水平相对丰度表 | XLS | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_network/genus.relative.xls) |
| Y.list | Y 组样本列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_network/Y.list) |
| Z.list | Z 组样本列表 | TXT | 16S/18S/ITS | 通用 | (${AMPLICON_ROOT}/examples/step4_network/Z.list) |

---

## 输出

| 文件名 | 描述 | 格式 | 适用组学 | 适用物种 | 示例文件 |
|--------|------|------|----------|----------|----------|
| Y/Shell/*.sh | Y 组网络分析脚本 | SH | 16S/18S/ITS | 通用 | - |
| Y/dot/igraph.calculate.txt | Y 组网络计算结果 | TXT | 16S/18S/ITS | 通用 | - |
| Y/dot/network.js | Y 组网络交互数据 | JS | 16S/18S/ITS | 通用 | - |
| Z/Shell/*.sh | Z 组网络分析脚本 | SH | 16S/18S/ITS | 通用 | - |
| Z/dot/igraph.calculate.txt | Z 组网络计算结果 | TXT | 16S/18S/ITS | 通用 | - |
| Z/dot/network.js | Z 组网络交互数据 | JS | 16S/18S/ITS | 通用 | - |

---

## 执行命令

**通用格式**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_network.sh -i genus.relative.xls -y Y.list -z Z.list
# 输出：Y/, Z/
```

**示例**：
```bash
bash ${AMPLICON_ROOT}/scripts/step4_network.sh -i genus.relative.xls -y Y.list -z Z.list
# 输出：Y/Shell/, Y/dot/, Z/Shell/, Z/dot/
```

### 参数说明

| 参数 | 说明 | 必需 | 默认值 | 示例 |
|------|------|------|--------|------|
| -i, --input | 属水平相对丰度表路径 | 是 | - | genus.relative.xls |
| -y, --y-list | Y 组样本列表路径 | 是 | - | Y.list |
| -z, --z-list | Z 组样本列表路径 | 是 | - | Z.list |

---

## 流程步骤

```
1️⃣ derep.pl（去冗余处理）
   ↓
2️⃣ get_g_table.pl（生成 OTU 表）
   ↓
3️⃣ network.pipelinev2.pl（网络分析，生成 Shell 脚本）
   ↓
4️⃣ tab_js.pl（生成网络交互数据）
```

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
bash step4_network.sh ...
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
| 报告生成 | Y/dot/network.js | 插入分析报告（交互式） |

---

## 相关文件

- **脚本位置**: `${AMPLICON_ROOT}/scripts/step4_network.sh`
- **参考文档**: `${AMPLICON_ROOT}/reference/step4_network.md`
- **示例数据**: `${AMPLICON_ROOT}/examples/step4_network/`

---

最后更新：2026-04-15
