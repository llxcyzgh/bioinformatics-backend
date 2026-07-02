# 智能追问 + 现生成单步工具 开发计划

> 分支：`feat/smart-clarify-toolgen`（从 `henry-dev` 切出）
> 起草日期：2026-06-23
> 关联：`INTENT_DOMAIN_REWORK_PLAN.md`（意图/领域分流 T1-T7，已完成）、`C:\Users\henry\.claude\plans\cuddly-inventing-frog.md`（per-sample 编排泛化，暂停，本计划 Phase 5 复用其 step 4）

---

## 0. 背景与目标

### 0.1 现状（已完成的基础）
- 领域分流 + 相关性闸（`DomainClassifier`）：`原始数据 + PCoA` 已能正确落入 **amplicon**（Fix B，commit `0255a6d`）。
- 域感知追问模板（`_domain_examples`）：CASE B/C 不再写死 amplicon（commit `0255a6d`）。
- 第二个活动库 **stats**（id=7）已就绪，多库场景可测（commit `315c35d`）。

### 0.2 这次要解决的诉求（用户原话精炼）
系统**不应仅凭手头工具判断**，而要**按生信常识判断**——用户心里并不知道系统有什么脚本。所以：

1. 「我有原始数据要做 PCoA」→ 系统判定这是**扩增子分析类任务**，但**单端/双端客观未知**，应**追问**（而不是默认双端直接出流水线）。
2. 若用户答**单端**：系统目前**没有现成单端流程**，但 LLM **有能力现生成一个单步脚本**补齐。此时应追问：「这块我本来干不了，但我是个聪明的系统，可以给你现生成一个脚本，要不要？」
3. 用户同意后：生成脚本 → **自动录入脚本库** → 与既有脚本**串成有效流水线** → 重新规划 → 上传执行。

### 0.3 用户明确的核心约束
- **生成产物 = 单步工具级脚本**（同 cutadapt/dada2 级别），**不是**一个把整条任务包圆的大脚本。
- 新脚本的**输入/输出必须能与既有脚本串成有效流水线**。
- 新脚本要**自动录入脚本库**（即写入 `Script` 表 + 落盘 .sh + 进入工具图）。
- **生成是通用常识驱动的，不预先设计具体工具**：系统不把"单端"或任何缺口映射到某个固定脚本。它用**通用生信常识提示词**理解意图、识别缺口；缺口确无现成工具时，由 LLM **当场决定**生成什么样的单步脚本来补。单端只是触发此通用机制的例子之一。计划里出现的 `amp-dada2-se` 一律按"LLM 可能产出的示例"理解，**不作预设规格**。
- **意图识别必须智能、不查类型表（核心）**：意图理解与追问由**常识意图代理（IntentAgent）**统一完成——它从生信一般常识判断信息够不够、不够则**一次问全所有"不定就跑偏"的关键问题**（如"什么数据？单/双端？要不要去引物？"），**不靠关键词→预设问题的映射，也不靠类型菜单驱动提问**。类型词表只在"够意图"时作翻译目标（抽 available/goal ID），不当理解依据。

---

## 1. 目标交互流程（用户视角剧本）

```
用户：我有原始数据要做 PCoA 分析
系统：听起来是扩增子分析。为了给你定准流程，一次性确认几件事：
      ① 你手上是什么数据？原始测序数据、ASV 表，还是已算好的距离矩阵？
      ② 若是原始数据，是单端还是双端测序？
      ③ 原始数据需要做引物切除吗？
      （双端我有现成流程；单端目前没有现成的，但可以临时给你生成一个。）
用户：单端原始数据，要去引物
系统：[IntentAgent: sufficient] 单端目前平台没有现成流程。不过我可以现生成一个
      「单端 DADA2 去噪」单步脚本来补齐，生成后就能接上物种注释、多样性、PCoA。
      要我现在生成吗？
用户：好
系统：[生成中… 已生成 amp-dada2-se 并录入脚本库]
      好了。基于单端数据 → 单端DADA2去噪 → 物种注释 → 特征表 → 多样性 → PCoA，
      规划出如下方案：[展示路径]。请上传你的单端 fastq 文件。
用户：[上传]
系统：[生成编排脚本 → 执行]
```

> 系统第一轮的追问由 IntentAgent 凭生信常识**一次问全**（不是只问单/双端），避免挤牙膏式多轮打散用户意图。单端只是触发"现生成"的例子；任何意图不全的查询都走同一条常识追问。

---

## 2. 代码地图（grounding：现状 / 是否要改）

| 环节 | 文件:位置 | 现状 | 本次是否改 |
|---|---|---|---|
| 领域分流 | `app/services/domain_classifier.py` | `原始数据+PCoA`→amplicon 已通 | 否 |
| **意图识别（新核心）** | `app/services/intent_agent.py`（新建）| 不存在 | **新建**（Phase 1：常识意图代理，取代下方旧解析器+预设追问）|
| 旧解析器 | `pkg/amplicon/llm_parser.py` `parse_natural_language` + `app/services/parser_service.py` | LLM 抽类型ID + confidence | **降级为兜底**（IntentAgent 失败时回退，不再主导）|
| 路由 | `app/services/chat_service.py:232` `_route_decision` | CASE A/B/C/D 预设追问 + CASE D 规划 | **改**（Phase 1：`sufficient?` → 问 `questions[]` / 规划；删预设追问分支，留规划分支与能力缺口）|
| chat() 解析接线 | `app/services/chat_service.py:485` | amplicon/非amplicon 分调解析器 | **改**（Phase 1：统一走 IntentAgent）|
| 类型词表 | `amplicon_tools.py` + `DataType` 表 | FASTQ_PAIR 等；已补 FASTQ_SINGLE | 用（IntentAgent 抽取 ID 时的翻译目标；FASTQ_SINGLE 保留，不当追问依据）|
| 工具图加载 | `app/services/domain_service.py:42` `get_domain_tools` | 读 `Script.where(domain_id, verified=1, is_active=1)` + 内存缓存 | 用（新脚本注册后 `invalidate`）|
| 规划器 | `app/services/planner_service.py:22` `plan_workflow` | BFS over DB 工具图；新工具进图后自动可用 | 用（Phase 4 重规划）|
| 根输入推导 | `app/services/domain_service.py:108` `resolve_required_files` | 从工具链推上传需求 | 用（Phase 4 验证 FASTQ_SINGLE 上传）|
| 既有 codegen | `app/services/chat_service.py:840` `_generate_script_with_llm` | 喂**既有**脚本内容给 LLM 拼大脚本 | 否（参考其模式，不复用）|
| 编排器-通用步 | `pkg/amplicon/orchestrator.py:379` `_build_single_command` | 非 per-sample 工具按 data_type 解析，**任意 tool_id 都行** | 用（amp-dada2-se 走这里）|
| 编排器-manifest | `pkg/amplicon/orchestrator.py:352` `_gen_dada2_step` + `:194` `if tool_id=="amp-dada2"` | 写死 tool_id | **改**（Phase 5：按 `_MANIFEST` 参数检测，让 amp-dada2-se 也走 manifest）|
| 编排器-FASTQ 解析 | `pkg/amplicon/orchestrator.py:87` `_resolve_fastq_pair_uploads` | 只认 FASTQ_PAIR（R1/R2 配对） | **改**（Phase 5：加 FASTQ_SINGLE 多文件解析）|
| per-sample 区 | `pkg/amplicon/orchestrator.py:304` `_gen_parallel_region` | 对 cutadapt/flash/frags-qc 之外 per-sample 工具 `raise ValueError` | **不改**（amp-dada2-se 非 per-sample，绕开；完整泛化见 cuddly-inventing-frog）|
| 脚本注册（克隆范式） | `migrate_seed.py:918` `seed_stats_domain` | 字段零偏差克隆：verified/is_active/call_params/call_outputs/per_sample/file_path | 参考（Phase 3 的注册契约照此）|
| Script 模型 | `app/models/script.py` | 字段齐全（verified/is_active/call_params/call_outputs/per_sample/domain_id/file_path/inputs/outputs）| 用 |

---

## 3. 架构设计

### 3.1 通用常识驱动的缺口补齐（**不**预先设计具体工具）

本计划的核心原则：**系统不预先把"单端"或任何缺口映射到某个固定脚本**。补齐工具是 LLM 在运行时、基于**通用生物信息常识**现场决定的。单端只是触发此通用机制的例子之一；将来任何"合理但平台缺工具"的任务都走同一条路。

处理分四层（第 1 层是智能意图识别，2-4 层落到平台类型系统）：

1. **意图识别——常识意图代理 IntentAgent（Phase 1 核心，取代旧解析器 + 预设追问）**：一次 LLM 调用，从**通用生信常识**判断信息是否足够确定一个可执行任务，三合一输出：
   ```json
   {
     "sufficient": false,                                       // 够不够规划
     "questions": ["什么数据？", "单端还是双端？", "要去引物吗？"],  // 不够时：一次问全关键问题
     "available_inputs": [],                                    // 够时才填：类型 ID（仅作翻译）
     "goal_types": [],                                          // 够时才填
     "reasoning": "..."                                         // 常识依据
   }
   ```
   - 够 → 抽 `available_inputs/goal_types`（类型 ID **仅作翻译**，理解过程不查表）；
   - 不够 → `questions[]`：**一次抛出所有"不定就跑偏"的关键问题**，避免挤牙膏多轮；只问必需项，不穷举；
   - 代理被喂：**平台能力大白话描述**（理解/提问用）+ 类型词表（抽取时翻译目标）。**理解与提问基于生信常识，不是机械查类型表**——所以换个模糊问法（如"帮我看样本能不能分开"）它也能给出恰当追问，而非只认"原始数据→单/双端"这一例。
2. **缺口识别**（Phase 2）：IntentAgent 判 `sufficient=true` 后，在当前域工具图上找路径；找不到 → 用通用常识判断是"合理任务、只是缺工具"还是"无意义"。
3. **现场生成（落地到平台类型系统）**（Phase 3）：LLM 决定**生成什么样的单步工具**来补这个缺口；提示词同时给出**数据类型词表 + 串链约束 + 执行模型约束**，让产物既能串进既有流水线、又能被编排器执行。
4. **串链 + 执行**（Phase 4-5）：注册 → 重规划 → 上传 → 执行。

> **执行模型约束（重要）**：现有编排器 `_gen_parallel_region`（`orchestrator.py:331-338`）对 cutadapt/flash/frags-qc 之外的 per-sample 工具会 `raise ValueError`。因此生成提示词要**引导 LLM 优先生成"非 per-sample / 吃 manifest / 一次性处理全部样本"形态的工具**（这种走通用 `_build_single_command` 分支，任意 tool_id 都能编排）。这是**约束 LLM 的形态偏好**，不是**替它选好工具**。

> **举例（非预设）**：对"单端原始数据 → PCoA"这个缺口，LLM 凭常识很可能决定生成一个「单端 DADA2 去噪」单步工具——把单端 raw fastq 经 manifest 一步变成下游能用的特征表/代表序列。但**这是 LLM 的判断，不是计划预设的产物**；换个缺口它会生成别的东西。下文 §3.2/§3.3 出现的 `amp-dada2-se` 字样均按此例理解，**仅作说明**。

### 3.2 生成产物契约 = 一个 `ScriptCallDef` + 一个 `.sh`

LLM 生成的不是"一段大脚本"，而是与 cutadapt/dada2 **同构的单步工具**。**`tool_id / inputs / outputs / params` 的具体取值由 LLM 在运行时按常识决定**——平台只规定结构契约与串链/执行约束（§3.1）。产出两样东西（以下以单端缺口为例，字段值仅作说明）：

**(a) `.sh` 脚本**（落盘到 `scripts/generated/amp-dada2-se.sh`，风格对齐既有 `step3_dada2.sh`）：
- `#!/bin/bash`，`set -euo pipefail`
- 参数解析（`getopts` 或 case），接受 `-m manifest.tsv` + 若干 `_CONFIG` 参数（如 `--trunc-qmin`、`--trunc-len`）
- 核心调用 `qiime dada2 denoise-single --i-demultiplexed-seqs ... --p-trunc-len ...`
- 输出 `featureSeqs.qza / featureTable.biom / feature.fasta`

**(b) JSON 契约**（写入 `Script` 行的 `call_params`/`call_outputs`/`inputs`/`outputs`/`per_sample`）：
```json
{
  "tool_id": "amp-dada2-se",
  "name": "单端DADA2去噪",
  "inputs": ["FASTQ_SINGLE"],
  "outputs": ["FEATURE_SEQS", "FEATURE_TABLE", "FEATURE_FASTA"],
  "call_params": [
    {"flag": "-m", "data_type": "_MANIFEST"},
    {"flag": "--trunc-len", "data_type": "_CONFIG", "default": "0", "required": false}
  ],
  "call_outputs": [
    {"data_type": "FEATURE_SEQS",   "filename": "featureSeqs.qza"},
    {"data_type": "FEATURE_TABLE",  "filename": "featureTable.biom"},
    {"data_type": "FEATURE_FASTA",  "filename": "feature.fasta"}
  ],
  "per_sample": 0,
  "category": "核心分析"
}
```

### 3.3 串链不变式（必须满足，否则注册前拒收）

> 新工具的**每个输出类型**，要么命中至少一个既有下游工具的**输入**，要么是用户目标类型。
> 这是对 **LLM 现场产物**的运行时校验（不预设具体工具）；不通过则拒收/要求重生成。

以下以单端缺口可能产出的「单端 DADA2 去噪」工具为例自检：

| 输出类型 | 被谁消费（既有工具） | 是否到达 PCoA |
|---|---|---|
| `FEATURE_SEQS` | `amp-taxonomy`(→TAXONOMY_ASSIGN)、`amp-phylogeny`(→ROOTED_TREE) | ✓ 经 phylogeny |
| `FEATURE_TABLE` | `amp-feature-tables`(→ASV_TABLE)、`amp-funpre` | ✓ 经 feature-tables |
| `FEATURE_FASTA` | `amp-genus-tree`、`amp-funpre` | （旁路）|

完整可达链：
```
FASTQ_SINGLE →[amp-dada2-se]→ FEATURE_SEQS + FEATURE_TABLE
  FEATURE_SEQS →[amp-phylogeny]→ ROOTED_TREE
  FEATURE_SEQS →[amp-taxonomy]→ TAXONOMY_ASSIGN
  FEATURE_TABLE + TAXONOMY_ASSIGN →[amp-feature-tables]→ ASV_TABLE
  ASV_TABLE →[amp-table-stats]→ ASV_TABLE_EVEN
  ASV_TABLE_EVEN + ROOTED_TREE →[amp-beta-data]→ PCOA_COORDS
  PCOA_COORDS →[amp-pcoa]→ PCOA_PLOT ✓
```
BFS 规划器应能自动找出此路径（Phase 4 验证）。

### 3.4 自动录入脚本库的契约

注册一行 `Script`（照 `seed_stats_domain` 克隆范式的字段集），关键点：
- `domain_id` = 当前任务领域（amplicon=1）
- `verified=1, is_active=1` → **立即进工具图**（`get_domain_tools` 的过滤条件）
- `tool_id` 全局唯一（生成时查重，已存在则复用而非重复生成）
- `inputs/outputs` = JSON 类型 ID 串（建图用）
- `call_params/call_outputs/per_sample` = 编排器调用所需（同 3.2）
- `file_path` = `Amplicon/generated/amp-dada2-se.sh`（相对 `$AMPLICON_ROOT`，编排器拼 `${AMPLICON_ROOT}/{file_path}`）
- 落盘 .sh 到 `scripts/Amplicon/generated/`（种子脚本在 `scripts/Amplicon/scripts/`，新生成的放 `generated/` 子目录与人工脚本隔离）
- 注册后 **`DomainService.invalidate(domain_id)`** 清工具图缓存，否则规划器看不到新工具

> 安全权衡：`verified=1` 跳过了"人工校验"环节（`Script` 注释里写明默认未启用需人工校验）。本特性的卖点正是"自动可用"，故接受；但生成脚本需过**契约校验 + 语法粗检**（Phase 3），并把 `uploaded_by` 记为系统/当前用户以便审计。

---

## 4. 分阶段实现

### Phase 1：常识意图代理（IntentAgent）——智能意图识别取代预设查表

**目标**：用**一次 LLM 常识推理**取代"解析器抽类型ID + route_decision 按ID有无选预设追问模板"。任意模糊查询，代理都从生信常识判断够不够、不够则**一次问全**所有关键问题。这是本计划"智能"的落点——**意图识别不查类型表**。

**改动**：
1. **新建 IntentAgent**（`app/services/intent_agent.py`）：
   - 输入：用户原话 + 对话历史 + 领域能力大白话描述（`Domain.description` 等）+ 类型词表（`get_type_vocab`，仅作抽取翻译目标）。
   - LLM（DashScope，`response_format=json_object`）输出：`{sufficient, questions[], available_inputs[], goal_types[], reasoning}`（schema 见 §3.1）。
   - prompt 硬约束：① 理解与提问基于**生信一般常识**，不机械查表、不靠关键词→预设问题映射；② 不够时 `questions` 只列"不定就跑偏"的关键项、**一次问全**、不穷举能默认的参数；③ 够时才抽类型 ID，且必须用词表内 ID；④ 给正反例（"原始数据做PCoA"→不够、问数据形态/单双端/引物；"双端原始数据做PCoA"→够）。
   - 失败兜底：LLM 不可用/解析失败 → 退回 `ParserService.parse`（旧解析器）+ 通用澄清，不崩。
2. **`chat()` 接线**（`chat_service.py:485` 附近）：amplicon / 非 amplicon **统一**走 IntentAgent（取代原 `ParserService.parse` 分支）；返回 `{sufficient, questions, available_inputs, goal_types, confidence}`。
3. **`_route_decision` 简化**（`chat_service.py:232`）：
   - `sufficient=false` → 返回 `type="clarification"`，`content` = 把 `questions` 组合成一条友好的多问题消息（**取代 CASE A/B/C/C-raw/D-low 所有预设追问分支**）；
   - `sufficient=true` → 用 `available_inputs/goal_types` 走规划（原 CASE D 流程：规划出路→方案；规划空→Phase 2 能力缺口）。
4. **回退 Phase 1 旧预设实现**：删 `_is_raw_data_ambiguous` / `_raw_data_layout_clarification` / CASE C-raw 分支；`llm_parser.SYSTEM_PROMPT`/`build_system_prompt` 里"原始数据→留白低置信"那条预设规则删掉（判断改由代理）；`parser_service.generate_raw_data_layout_clarification` 删。**保留**：`FASTQ_SINGLE` 类型（词表合法类型，代理抽取可用 + 将来生成工具的输入）、`ensure_data_type` 迁移、CASE D 规划分支。

**验证**：
- IntentAgent 直调三组：`我有原始数据要做PCoA` → `sufficient=false` + `questions` 含数据形态/单双端/引物等多条；`我有双端原始数据做PCoA` → `sufficient=true` + `available=[FASTQ_PAIR]`；`帮我看看样本能不能分开`（换模糊问法）→ 也能给出**恰当的常识追问**（证明不是只认单端这例）。
- 端到端 `chat()`：模糊查询一次问全、不再直接出双端流水线；双端照常规划（回归）。
- 兜底：临时禁用 LLM key → 退回旧解析器 + 通用澄清，不崩。

**风险**：
- 代理 `sufficient` 判断不稳：偶发"够判不够"（多问一轮，可接受）或"不够判够"（规划空→落 Phase 2 能力缺口，有兜底）。低温度 + 明确判定标准 + 正反例缓解。
- 过问/漏问：prompt 限定"只问必需项" + 抽查 questions 条数/质量。
- 成本/延迟：一次 LLM 调用承担原"解析+澄清"两步，净调用数不增；低温度控延迟。

---

### Phase 2：能力缺口识别——"合理但做不了"

**目标**：用户答单端后，规划器返回空（无 FASTQ_SINGLE 根的路径）→ 不要走"暂时无法找到方案"通用兜底，而是判定这是**合理但缺工具**的缺口。

**改动**：
1. **`_route_decision` 的 no-candidates 分支**（`chat_service.py:304`）前插一层：
   - 调用新方法 `_classify_capability_gap(db, domain_id, available, goals, content)`：
     - LLM 单次判定：「给定该领域、用户数据描述、目标，这是不是一个**合理的生信任务、只是平台当前缺对应工具**？」输出 `{plausible: bool, missing_link: str}`（如 `missing_link="FASTQ_SINGLE → FEATURE_TABLE"`）
     - `plausible=true` → 返回 `type="capability_gap"`（带 `missing_link`、`domain_id`、`available/goal_types`），交给 Phase 3 的提议分支
     - `plausible=false` → 维持现有通用兜底
2. 解析用户答"单端"的回合：`available=["FASTQ_SINGLE"]`、`goals=[PCOA_PLOT]` → 规划器空 → `_classify_capability_gap` 判 plausible → 进入提议。

**验证**：
- 构造 `available=["FASTQ_SINGLE"], goals=["PCOA_PLOT"]` 调 `plan_workflow` → 空。
- `_classify_capability_gap` 对此返回 `plausible=true, missing_link≈"FASTQ_SINGLE→FEATURE_TABLE/去噪"`。
- 对照：`available=["FASTQ_PAIR"], goals=["PCOA_PLOT"]` 应能规划出路径（非缺口）。

**风险**：LLM 把无意义输入也判成 plausible → 提议生成垃圾脚本。用低 temperature + 给反例（天气/闲聊）压制；生成的脚本还要过 Phase 3 契约校验兜底。

---

### Phase 3：现生成单步工具 + 自动录入（核心）

**目标**：用户同意后，生成 `amp-dada2-se`（.sh + 契约），校验串链，落盘 + 写 `Script` 行 + 清缓存。

**改动**：新建 `app/services/tool_genesis_service.py`：

```
class ToolGenesisService:
    @staticmethod
    def generate_and_register(db, domain_id, gap_spec, user_id) -> dict:
        # 1) 查重：tool_id 已存在且 active → 直接复用，不重复生成
        # 2) LLM 现场生成（通用生信常识 + 平台约束；不预设生成什么工具）：
        #    system: "你是生信脚本工程师。基于通用生物信息常识，判断这个缺口需要什么样的
        #             【单步】工具，再生成它的 bash 脚本 + I/O 契约 JSON。只做一步，
        #             不要拼整条流水线。"
        #    约束（写进 prompt）：① 输入/输出必须用平台词表里的类型 ID（附词表）；
        #             ② 每个 output 必须能被既有工具消费或是用户目标（串链不变式 §3.3）；
        #             ③ 优先生成【非 per-sample / 吃 manifest】形态，以适配现有编排器
        #               （per-sample 工具当前无法被编排，见 §3.1 执行模型约束）。
        #    user: 缺口描述（用户意图 + 缺的环节，Phase 2 给出）+ 平台类型词表
        #          + 既有同族脚本片段作风格 few-shot（可选）
        #    response_format: json_object，含 {sh_content, contract}
        # 3) 契约校验（不过则报错、不注册）：
        #    - tool_id 合法且唯一
        #    - outputs 非空，且每个 output 命中"既有下游输入 ∪ 用户目标"（串链不变式 3.3）
        #    - inputs/outputs/call_params/call_outputs 结构合法
        #    - sh_content 粗检：含 #!/bin/bash、核心命令（denoise-single）、参数解析
        # 4) 落盘 sh_content → scripts/Amplicon/generated/<tool_id>.sh
        # 5) 写 Script 行（verified=1,is_active=1,domain_id,...照 3.4 契约）
        # 6) DomainService.invalidate(domain_id)
        # 7) 返回 {tool_id, script_id, tool_chain_preview}
```

**`_route_decision` 加提议分支**（接 Phase 2 的 `capability_gap`）。严格遵循「**先自动判定 → 提示用户 → 得到回复后才生成**」：
- 首次缺口 → `type="offer_codegen"`：文案「这块我本来干不了，但我可以现生成一个 `<missing_link>` 的单步脚本，生成后就能接上既有流程。要吗？」+ 按钮
- 用户同意（新一轮 chat，带同意信号）→ 调 `ToolGenesisService.generate_and_register` → 拿到新 tool_id → **立刻 Phase 4 重规划** → 回 `type="workflow"` 展示含新工具的路径

**验证**：
- 直接调 `generate_and_register(domain_id=1, gap_spec={...FASTQ_SINGLE→FEATURE_TABLE...})`：
  - `scripts/Amplicon/generated/amp-dada2-se.sh` 落盘且可读
  - DB 多一行 `Script(tool_id=amp-dada2-se, verified=1, is_active=1, domain_id=1)`
  - `DomainService.get_domain_tools(db, 1)` 现在含 `amp-dada2-se`
- 串链不变式：注册前校验 `outputs ⊆ (下游输入 ∪ 目标)`，不满足则拒注。
- 幂等：同 gap 第二次调用 → 查重命中 → 复用，不重写 .sh / 不新增行。

**风险**：
- LLM 生成脚本的**可靠性**：无完整参考（单端 dada2 没现成脚本）→ 较自由 → 可能产出跑不起来的脚本。缓解：喂 `step3_dada2.sh` 作风格 few-shot + 契约/语法粗检 + 执行失败时如实报错（编排器已有 `algo_error` 机制 `chat_service.py:1103`）。
- 跳过人工 `verified`：接受（卖点是自动可用），但 `uploaded_by` 记系统用户、`description` 标注「LLM 现生成」便于审计/回滚。

---

### Phase 4：重新规划 + 串链/上传验证

**目标**：注册后重新跑规划器，确认含 `amp-dada2-se` 的路径出现、前端路径图能展示、`resolve_required_files` 推出 `FASTQ_SINGLE` 上传需求。

**改动**：基本无新代码（机制已具备），主要是接线和验证：
- Phase 3 注册后，`PlannerService.plan_workflow(db, 1, ["FASTQ_SINGLE"], ["PCOA_PLOT"])` 应返回含 `amp-dada2-se` 的候选。
- `_enrich`（`planner_service.py:41`）会从 DB 补展示属性；`per_sample` 当前从静态 `TOOL_SCRIPT_CALLS` 取（`planner_service.py:72`）→ amp-dada2-se 不在其中 → `per_sample=False`（正确，它非 per-sample）。**无需改 `_enrich`**。
- `DomainService.resolve_required_files(db, 1, [tool_chain])` → 应推出 `FASTQ_SINGLE`（multiple=True）的上传需求。
- 前端路径图：新节点 `amp-dada2-se` 走通用渲染（与 stats 域克隆脚本同路径），无需前端改。

**验证**：
- 规划出路径，tool_chain 头部是新生成的工具（如 `amp-dada2-se`），尾部是 `amp-pcoa`。
- `resolve_required_files` 含 `{typeId:"FASTQ_SINGLE", multiple:true, extensions:[.fastq,.fastq.gz]}`。
- 路径图 API `/api/.../graph` 含新节点 + 它到 `amp-taxonomy`/`amp-feature-tables` 的边（类型 `FEATURE_SEQS`/`FEATURE_TABLE`）。

---

### Phase 5：执行支持（让 LLM 生成的 manifest 形态单步工具真能跑）

**目标**：上传原始数据 → 生成编排脚本（manifest 正确）→ 执行。这是把 demo 从"规划出路径"推进到"真出结果"的收尾。Phase 5 **不写任何工具脚本**（那是 Phase 3 的 LLM 干的），只让编排器能调度 LLM 生成的（按 §3.1 引导、吃 manifest 形态的）单步工具。

**改动**（编排器两处小改，**不做**完整 per-sample 泛化）：
1. **FASTQ_SINGLE 上传解析**（`orchestrator.py:87` `_resolve_fastq_pair_uploads` 旁加 `_resolve_fastq_single_uploads`）：
   - 把所有单端 fastq 上传文件 → `samples: {sample_name: {"SE": stored}}`
   - `generate_orchestrator_script` 里 `if FASTQ_SINGLE in required_files` 分支：建 `samples` + 不拆 R1/R2
2. **manifest 步骤泛化**（`orchestrator.py:194`）：
   - 现状：`if tool_id == "amp-dada2"` → `_gen_dada2_step`
   - 改：`if any(p.data_type == "_MANIFEST" for p in call_def.params)` → `_gen_manifest_step(...)`
   - `_gen_manifest_step` 按 `samples`（单端用 `{"SE": path}`，双端用 `{sample}.fastq`）写 manifest 行；其余同现状
   - （这正是 `cuddly-inventing-frog.md` 的 step 4，单点复用，不引入整个暂停计划）

> 注：若 LLM 偏偏生成了 per-sample 形态工具（违反 §3.1 引导），编排器仍会 `ValueError`——此时如实报错并提示需 per-sample 泛化（cuddly-inventing-frog），不静默。

**验证**：
- 上传 2 个单端 fastq → `confirm_upload` → `script1`（算法编排）成功生成（不抛 ValueError），含 manifest 行 + `amp-dada2-se` 调用。
- `shellcheck`（若有）生成脚本无语法错。
- 真实执行（若有 Docker/SGE 环境）：跑通到 PCoA；无环境则停在"编排脚本已生成"并如实标注。

**风险**：manifest 单端/双端分支易写错 → 用单元化的小数据集（1-2 样本）端到端冒烟。

---

## 5. 串链不变式自检清单（Phase 3 注册前强制）

- [ ] `tool_id` 在该 domain 内唯一（查 `Script.where(domain_id, tool_id)`）
- [ ] `outputs` 每项 ∈ {既有工具 inputs 的并集} ∪ {用户目标类型}
- [ ] `inputs` 至少含一个可上传根类型（`FASTQ_SINGLE`）或可由上游产出
- [ ] `call_params` 里需 manifest 的工具有 `_MANIFEST` 参数；`call_outputs` 的 filename 与 .sh 实际产出一致
- [ ] `.sh` 含 `#!/bin/bash`、参数解析、核心命令；`bash -n` 语法过

---

## 6. 风险与决策点

| 风险 | 缓解 |
|---|---|
| LLM 生成脚本不可运行 | few-shot 喂同族脚本 + 契约/语法校验 + 执行失败如实报错（不静默） |
| `verified=1` 跳过人工校验 | `uploaded_by`=系统、`description` 标注「LLM 现生成」、落盘 `generated/` 与人工脚本隔离、可一键软删 |
| 缺口误判（闲聊也被提议生成） | Phase 2 LLM 低温度 + 反例；Phase 3 契约校验兜底 |
| 解析器"不默认双端"影响存量话术 | （已作废：该预设方案被 IntentAgent 取代）|
| IntentAgent `sufficient` 误判 | 低温度 + 正反例；"不够判够"有 Phase 2 能力缺口兜底，"够判不够"至多多问一轮 |
| 过问/漏问（questions 质量） | prompt 限定只问必需项 + 抽查；多轮对话累积上下文减少重复问 |
| 单端科学性（仅短读区成立） | 用户主动选单端即默认成立；可在追问文案里一句话提示 |

**待用户拍板**（非阻塞，先按推荐做）：
- 生成脚本落盘目录：推荐 `scripts/Amplicon/generated/`（与 `scripts/` 隔离）。
- 首版一次缺口只生成**单个**补齐工具（具体是什么由 LLM 当场决定）；多工具编排留后续。

---

## 7. 验证策略（无测试框架）

每 Phase 用一次性 Python 脚本（放 `scripts/uploaded/` 或临时文件，gitignore）直调服务层，绕过 HTTP：

- **P1**：IntentAgent 直调三组话术（模糊→`sufficient=false`+多 questions / 双端→`sufficient=true`+FASTQ_PAIR / 换个模糊问法也能给出常识追问）；`chat()` 看一次问全；禁 key 兜底不崩。
- **P2**：`plan_workflow(FASTQ_SINGLE, PCOA_PLOT)==[]` + `_classify_capability_gap==plausible`。
- **P3**：`generate_and_register` → 查 .sh 落盘 + DB 行 + `get_domain_tools` 含新工具 + 第二次调用幂等。
- **P4**：`plan_workflow` 出含 amp-dada2-se 路径 + `resolve_required_files` 推出 FASTQ_SINGLE。
- **P5**：`confirm_upload`（mock 单端上传）→ `script1` 生成无异常 + manifest 行正确。

端到端：前端登录 → 对话「原始数据做PCoA」→ 追问 → 答单端 → 提议 → 同意 → 见路径 → 上传 → 见编排脚本。

---

## 8. 不做（Non-goals）

- **完整 per-sample 编排泛化**（cutadapt-se/flash-se 等 per-sample 生成工具）：见 `cuddly-inventing-frog.md`，本计划只用其 step 4（manifest 泛化），amp-dada2-se 靠"非 per-sample"绕开其余。
- **多生成工具的编排**：首版单工具补齐。
- **生成脚本的前端管理/审计 UI**：DB 行 + 软删即可，UI 后续。
- **RBAC / 生成权限控制**：已知占位（见 known-placeholder-features），不在本计划。
- **不改领域分流**（`DomainClassifier`）：IntentAgent 在领域已钉之后运行，不接管"归哪个领域"的判断；领域间消歧/相关性闸仍走 T3-T5。

---

## 9. 与既有计划/记忆的关系

- 继承 `INTENT_DOMAIN_REWORK_PLAN.md` 的 T1-T7 成果（领域分流、相关性闸、stats 域）。本计划是其在"单领域内能力缺口"维度上的延伸。
- 复用 `cuddly-inventing-frog.md`（per-sample 泛化，暂停）的 **step 4**（manifest 按 `_MANIFEST` 检测），不复活整个计划。
- 不触碰已知占位（RBAC/JWT/admin 任务列表/admin 反馈/new.tsx）——审计别当 bug。
- 后端启动用 `.venv/Scripts/python.exe -m uvicorn`；查 .env 先 `load_dotenv()`；SGE→env 仍是 deferred，不动。

---

## 10. 推荐执行顺序

**P1 → P2 → P3 → P4 → P5**，每 Phase 可独立验证、独立提交。

- P1+P2 把"IntentAgent 智能追问 + 缺口识别"跑通（无需生成脚本即可演示智能意图识别）。
- P3+P4 是核心（生成 + 注册 + 串链 + 重规划），跑通后即可演示"现生成工具并接入流水线"。
- P5 让 demo 真能执行（到 PCoA），收尾。

首版可停在 P4（规划出含新工具的路径 + 上传需求），P5 视执行环境有无再定。
