# 独立单步分析闭环（Path B）开发计划

> 起草日期：2026-07-08
> 关联：`SMART_CLARIFY_TOOLGEN_PLAN.md`（多步管线的缺口补齐 ToolGenesis，已完成 P1–P4）、`INTENT_DOMAIN_REWORK_PLAN.md`（意图/领域分流 T1–T7，已完成）、根目录 `智能分析平台_对话示例.html`（客户给的 5 个示例，本计划的需求来源）
> 本文件为**上下文压缩后自助执行**而写，自包含。

---

## 0. 背景：为什么单独开一条路

客户根目录的 `智能分析平台_对话示例.html` 给了 5 个用户问法（热图 / 生存分析 / 火山图 / 组间比较 / Lasso 回归），体现两个诉求：

1. **模糊时像专家一样追问**：用户不知道系统能干什么、也未必能精确描述。系统要像生信专家对待小白——耐心但有效地问。
2. **现有工具干不了→现场生成代码**：弄清要干什么后，当场生成一个脚本解决。客户很有信心，因为"对任何模型说生成 xx 脚本都能生成得很好"。

核查结论（见对话）：这 5 个分析**工具库里一个都没有**（最接近的 `amp-taxasummary`/`amp-ttest` 是扩增子微生物数据上的，领域不同）。但**两个能力都已有半成品**：诉求① = `IntentAgent`（已上线）；诉求② = `IntentAgent.classify_capability_gap` + `ToolGenesisService`（已上线，端到端通）。

**关键区分（已与用户对齐）**：

| 路 | 单位 | 何时用 | 产物 |
|---|---|---|---|
| 老路（planner） | 工具图上一条**路径** | 多步、已有工具可串（16S→…→PCoA） | 缝合多个已有 `.sh` |
| ToolGenesis | 工具图上**一个 typed 节点** | 多步链里**缺一个节点**（单端 dada2） | 生成 typed 工具，过串链不变式，进图重规划 |
| **Path B（本计划）** | **一个自包含脚本** | **单步**、一个脚本就能搞定（生存分析/火山图…） | 生成成品脚本：文件进→文件出，无类型系统/串链/编排 |

> ToolGenesis 生成的是"零件"，Path B 生成的是"成品"。客户那句"模型随便生成"成立的**前提是生成自包含脚本（B）**，不是生成符合平台类型系统的可串链工具（ToolGenesis）。

**用户明确的前提（路由闸）**：B 只接「一个脚本就能解决、不需要临时编制复杂工作流」的任务。需要复杂工作流的仍走老路/ToolGenesis。

---

## 1. 三选一第一级路由（本计划的骨架）

一句话进系统后，第一级分三叉：

1. **不是生信** → `out_of_scope`（已有，`_out_of_scope_response`）
2. **生信 + 多步流水线** → typed 领域 + IntentAgent + planner（已有；缺口走 ToolGenesis）
3. **生信 + 单步独立分析** → **Path B（本计划）**

2 与 3 的区分由**形态判定器 `classify_form`**（新增，一次廉价 LLM 调用）完成。判定保守：拿不准归多步（老路有 ToolGenesis 兜底，更安全）。

> 5 个示例目前连第一级都过不去——`stats` 域(id=7)的关键词还是微生物那套（相对丰度/距离矩阵/PCA），"生存分析/火山图/基因表达"哪个 typed 域都不认，会被当 out_of_scope。**B 路正是这些"合理生信但不属于任何 typed 工具域"的查询的归宿**：B 不依赖 typed 域，靠模型通用知识即可。

---

## 2. B 的闭环（用户视角剧本，对齐客户 HTML）

```
用户：我想做生存分析，看看 TP53 高低表达组的生存差异
系统：[形态=单步 + 信息够] 📋 生存分析需要你提供：
        1. 临床数据 [必需]  列：OS_time(总生存月数)、OS_status(0存活/1死亡)  TSV
        2. 基因表达 [可选]  用于按高/低表达自动分组  TSV
      可选参数：分组方法(默认中位数)、分析类型(默认 KM 曲线)
      请上传临床数据文件。（v1 渲染成 markdown 文本气泡）
用户：[上传 clinical_data.tsv + gene_expression.tsv]  用中位数分组，画 KM 曲线
系统：[现生成自包含 survival_km.R → 归档为模板 → 提交执行]
      脚本已生成并归档（模板 ID: ...）。正在执行……
系统：[执行完成/模拟] 结果：km_curve.pdf + 统计摘要。📥 下载脚本 📥 下载结果
      💡 下次可直接说"用生存分析模板分析新数据"
```

对比老路：**没有 confirm-path、没有路径图、没有多步编排**。闭环 = 清单 → 上传 → 生成单脚本 → 执行 → 归档。

---

## 3. 代码地图（grounding：现状 / 是否改）

| 环节 | 文件:位置 | 现状 | 本次 |
|---|---|---|---|
| 相关性闸 | `app/services/domain_classifier.py` `classify_with_relevance` | 判 in_scope + domain_id/none + confidence | **改**：区分"合理生信但无 typed 域"（→ B 候选）与"非生信"（→ out_of_scope） |
| 第一级 dispatch | `app/services/chat_service.py:602-630` | domain→IntentAgent；无域→out_of_scope/uncertain/disambiguate | **改**：插入形态判定，single→B 路 |
| IntentAgent（多步理解） | `app/services/intent_agent.py` `understand` | typed sufficient/questions/available/goal | **不动**（B 不复用它，避免污染稳定的多步路径） |
| 路由 | `chat_service.py:209` `_route_decision` | sufficient?→规划/缺口/兜底 | **不动**（B 不走这里） |
| 默认路由入口 | `chat_service.py:285` `_default_intent_route` | IntentAgent→_route_decision | **改**：旁边加 B 分支 `_standalone_route` |
| **形态判定器** | （新）`app/services/analysis_router.py` | 不存在 | **新建** `classify_form` |
| **B 理解+清单** | （新）`app/services/standalone_analysis_agent.py` | 不存在 | **新建**：understand→analysis_type+data_requirements+params+questions |
| **B 脚本生成+归档** | （新）`app/services/standalone_script_service.py` | 不存在 | **新建**：生成自包含脚本 + 写 Script 模板行 |
| 文件上传/校验 | `chat_service.py:1215` `confirm_upload` + `file_request` 消息 | 按 required_files 校验扩展名 | **复用**（B 的 required_files 来自 data_requirements） |
| 执行 staging | `chat_service.py:1613` `simulate_execution` / `1416` `start_execution` | 写脚本到 `/shared`→`docker exec sge-master qsub` | **复用模式**（B 单脚本版，见 §4.4） |
| 多步 codegen | `chat_service.py:669` `confirm_path` / `856` `_generate_orchestrator_with_llm` | LLM 拼编排脚本 | **B 不用** |
| planner/orchestrator | `planner_service.py` / `pkg/amplicon/orchestrator.py` | 工具图 BFS + 缝脚本 | **B 不用** |
| ToolGenesis | `tool_genesis_service.py` `generate_and_register` | 生成 typed 节点+串链校验+入库 | **不动**（留给多步缺口） |
| 归档 | `Script` 表（参考 `tool_genesis_service._persist`） | 写 tool_id/inputs/outputs/... | **复用**（B 写为"独立模板"行） |
| 前端消息渲染 | `frontend/src/pages/user/tasks/[uuid]/show.tsx:458-474` | workflow→路径图 / file_request→上传 / clarification→文本 | v1 **复用** clarification+file_request；v2 **新增** 富清单类型 |
| 路由端点 | `routes/chat.py` | chat/confirm-path/confirm-upload/start-execution/simulate-execution/... | v1 **复用**；v2 视情况加 `/standalone-generate` |

---

## 4. 架构设计

### 4.1 三级路由 + 形态判定器

在相关性闸之后、typed 理解之前，插入形态判定：

```
verdict = classify_with_relevance(content)        # 已有
if not verdict.plausible_bioinfo:  → out_of_scope  # 已有（区分"非生信"）
else:
    form = AnalysisRouter.classify_form(content, verdict)   # 新增：单步/多步
    if form == "standalone":
        → _standalone_route(...)                  # B 路（新）：先召回模板，命中则复用，未命中才生成
    else:
        if verdict.domain_id 已钉: → IntentAgent → planner（已有）
        else: → _uncertain/_disambiguate（已有）
```

**`AnalysisRouter.classify_form`**：一次 LLM（temperature 0，`response_format json_object`），prompt 给"单步=一个脚本文件进文件出即可；多步=要多个工具串成流水线"的定义 + 正反例（生存分析/火山图/热图→单步；16S 原始数据到 PCoA→多步）。输出 `{form: "standalone"|"pipeline", reasoning}`。无 key/失败 → 保守判 `pipeline`（走老路，有兜底）。

> 设计选择（已在对话中定）：形态判定独立成一步，**不**塞进 IntentAgent。理由：IntentAgent 是 typed、amplicon 调过、稳定；B 是 untyped、靠通用知识。分开两条路风险更低。代价：多步场景多一次廉价分类调用——可接受（后续可优化为"高置信 amplicon 域跳过判定"）。

### 4.2 StandaloneAnalysisAgent（理解 + 清单）

`understand(content, history) -> dict`，一次 LLM，输出：

```json
{
  "sufficient": true,
  "questions": [],
  "analysis_type": "Kaplan-Meier 生存分析",
  "data_requirements": [
    {"key": "clinical", "label": "临床数据", "required": true,
     "format": "TSV", "columns": ["OS_time","OS_status"], "columns_desc": "OS_time=总生存月数, OS_status=0存活/1死亡",
     "multiple": false},
    {"key": "expression", "label": "基因表达", "required": false, "format": "TSV", "columns": ["TP53_expr"], "multiple": false}
  ],
  "params": [
    {"key": "group_method", "label": "分组方法", "default": "中位数", "options": ["中位数","最优截断值","自定义"]},
    {"key": "analysis_type", "label": "分析类型", "default": "KM曲线", "options": ["KM曲线","Cox单因素","Cox多因素"]}
  ],
  "runtime_hint": "R / survival + survminer"
}
```

- sufficient=false → `questions[]`（走 §4.3 追问，复用 `_route_decision` 的"一次问全"文案风格）。
- prompt 硬约束：① 基于通用生信常识判断信息够不够；② 够时 `data_requirements` 列全"不定就跑偏"的必需输入 + 合理默认参数，**不要挤牙膏**；③ `columns`/`format` 精确（这是客户清单的核心），用大白话，不出现内部代号；④ 不替用户默认数据形态（沿用 IntentAgent 的首要规则）。
- 失败兜底：`sufficient=false` + 通用两问（数据/目标），不崩。

### 4.3 B 的回复消息（v1 零前端改动）

`_standalone_route` 产出的助手消息：

- **信息够** → `type="clarification"`，`content` = markdown 渲染的清单（必需/可选 tag、列名、格式、参数默认值），`data` = `{standalone: true, data_requirements, params, analysis_type}`。前端按文本气泡渲染 markdown（已支持），**无需改前端**。同时把 `data_requirements` 转成 `required_files` 形态，写一条 `type="file_request"` 消息触发既有上传面板（`show.tsx:2538 fileUpload`）。
- **信息不够** → `type="clarification"`，`content` = 编号追问清单（同 IntentAgent 风格）。

> v1 故意复用 `clarification`/`file_request`：用最小改动把闭环跑通、可演示。富交互清单（必需/可选彩色 tag、列说明 tooltip、参数下拉、示例文件下载）留 v2（§5 P5）。

### 4.4 StandaloneScriptService（生成 + 归档 + 执行）

**生成** `generate(analysis_type, data_requirements, params, file_mapping, content) -> dict`：
- 一次 LLM（temperature 0.2，`response_format json_object`），system："你是生信脚本工程师。生成一个**自包含**的 {runtime_hint} 脚本，直接读取下列输入文件（按给定列名/格式）、产出结果文件。不要依赖平台类型系统、不要写多步串联。参数按用户选择/默认。脚本要真能跑（真实工具命令，禁止 cp/touch 伪造）。"
- user：analysis_type + data_requirements（列/格式）+ params（用户选的值）+ 用户原话 +（可选）同语言 few-shot 片段。
- 输出 `{sh_content, outputs: [{filename, desc}], language: "R"|"python"}`。
- 校验：非空、含 shebang/真实命令、`outputs` 文件名合法。R 脚本过 `Rscript -e 'parse(file=...)'` 粗检（若本机有 R）；无 R 则只做正则粗检 + 如实备注。

**归档**（复用 `Script` 表，参考 `tool_genesis_service._persist`）——**关键是存全契约,使其可召回可重放**:
- 写一行 `Script`：`tool_id = "standalone-<slug>"`（查重，已存在则复用）、`domain_id = <stats 或独立分析域>`、`verified=1, is_active=1`、`file_path = "standalone/generated/<slug>.{R|py}"`、`inputs/outputs` = JSON（文件级，非 typed）、`description` 标注「LLM 现生成·独立分析模板」、`uploaded_by = user_id`。
- **额外存召回+重放所需的完整契约**（塞 `md_content` JSON 或新增 `standalone_meta` 字段）：`analysis_type`(规范名)、`aliases`(别名/同义词列表,如 ["生存分析","生存曲线","KM","预后"])、`data_requirements`、`params`、`runtime_hint`、生成时的用户原话片段。这样下次命中后能**原样重放清单**,而不是重生成。
- 落盘到 `scripts/standalone/generated/`（与 amplicon 隔离）。
- 归档的意义=可被下次召回复用（见 §4.6），不只是文件存储。

**执行**（复用 simulate 的 staging，单脚本版）：
- 把生成脚本写到 `${SHARED_DIR}/task_<tid>/run.{sh|R}`（含输入文件软链/路径注入），通过 `docker exec sge-master qsub` 提交（同 `simulate_execution:1694-1700`）；复用 `ExecutionService.create/start/fail` + `get_execution_logs` 轮询。
- **如实约束**：真实出图依赖 ① SGE docker 容器在跑 ② 容器内装了 R + survival/survminer/ggplot2/glmnet/pheatmap。无环境则停在"脚本已生成并归档"，标注"执行需 R 环境（deferred，同 amplicon）"，提供脚本下载。**绝不静默伪造结果**。

### 4.5 复用什么、跳过什么

- **复用**：相关性闸、`confirm_upload`（文件校验）、`simulate/start_execution` 的 staging + `ExecutionService` + 日志轮询、`Script` 表归档、前端文本气泡/上传面板渲染。
- **跳过**：IntentAgent（typed 理解）、`_route_decision`、planner、orchestrator、typed 工具图、串链不变式、ToolGenesis、confirm_path。

### 4.6 模板召回（归档的意义所在 —— 必做，不deferred）

> 没有召回，归档就是死文件。`_standalone_route` 的**第一步**就是召回，命中则复用、未命中才生成。这是 B 闭环的一等公民，不进 non-goals。

**召回时机**：form 判定为 standalone 之后、`StandaloneAnalysisAgent.understand` 之前（或合并到同一次调用）。

**召回方法（retrieve-then-judge，LLM 判定）**：
- 取该域下所有 `is_active=1` 的 standalone 模板（`Script.where(domain_id, tool_id like 'standalone-%')`），每条提取 `analysis_type + aliases + 数据形态摘要`（基数小，几十种量级）。
- 一次 LLM（temperature 0，`response_format json_object`）：给用户原话 + 候选模板清单，输出 `{match: "standalone-<slug>" | null, confidence: high|medium|low, reason}`。
- prompt 约束：只在高置信同义匹配时返回 slug（"生存分析"≈"KM 生存曲线"≈"预后差异"），拿不准返回 null（宁可重新生成，不要错配）。

**命中（match≠null, confidence=high）**：
- **原样重放**该模板存的 `data_requirements`/`params` 作为清单（用户看到和上次一致的数据要求），不重新 LLM 生成清单。
- 明说"我之前生成过一个【{analysis_type}】模板，直接用它"。
- 脚本侧：默认复用已归档 `.sh`（幂等）；若用户改了参数 → 用模板作 few-shot 微调重生成，落同名覆盖。

**未命中/低置信（match=null）**：
- 走 `StandaloneAnalysisAgent.understand` 从头生成清单 + `StandaloneScriptService.generate` 生成脚本 → **归档**（写全契约，含 aliases）。下一次同类问法就能被召回。靠 `analysis_type` 去重，避免近重复模板堆积。

> 为什么不用关键词/embedding：自然语言变体多（生存分析/生存曲线/KM/预后），关键词会漏；而模板基数小，LLM 判定便宜且鲁棒，无需向量库。embedding 召回留待模板数过百再说。

> 失败兜底：召回 LLM 不可用 → 视为未命中（从头生成 + 归档），不阻断 B 闭环。

---

## 5. 分阶段实现（每阶段独立可验、独立可提交）

### P1：形态判定器 + 路由分叉（骨架） ✅ 已完成（2026-07-08，验证全过）
- 新建 `analysis_router.py` `classify_form`；在 `chat()` dispatch（602-630）插分叉：plausible_bioinfo 且 single → `_standalone_route`（先返回占位："这看起来是一个独立的单步分析（{analysis_type}），我来告诉你需要准备什么数据。"）；multi/out → 原逻辑。
- 扩展 `classify_with_relevance`：区分"合理生信无 typed 域"（plausible_bioinfo=true, domain_id=None）与"非生信"。
- **验证**：5 个示例 → single + 进 B 占位；"16S 原始数据做 PCoA" → multi + 老 IntentAgent（回归）；"今天天气" → out_of_scope（回归）；断 key → single 降级 multi 不崩。

### P2：B 理解 + 数据清单 + 模板召回 ✅ 已完成（2026-07-08，验证全过）
- 新建 `standalone_analysis_agent.py` `understand`（§4.2 schema）；`_standalone_route` 接上：**先召回（§4.6）** → 命中则重放模板清单、未命中才 `understand` 生成；sufficient→清单消息（clarification+file_request）；不够→追问。
- **验证**：直调 `understand("我想做生存分析...")` → `analysis_type≈KM生存`、`data_requirements` 含 OS_time/OS_status（精确列名）、`params` 含分组方法；"画个热图"→ 表达矩阵/分组/聚类方式；端到端 `chat()` 出清单 markdown；信息不全→一次问全。**召回**：先归档一个生存分析模板，再用变体问法("做个生存曲线"/"看TP53预后")→ 命中并重放同一清单；用无关问法→ 未命中、新生成。

### P3：脚本生成 + 归档（存全契约） ✅ 已完成（2026-07-08，验证全过；含 round-trip 召回）
- 新建 `standalone_script_service.py` `generate`（§4.4）；落盘 + 写 Script 模板行（**含 analysis_type/aliases/data_requirements/params 完整契约**，供召回重放）；幂等（同 analysis_type 复用）。
- **验证**：`generate("生存分析", ...)` → `scripts/standalone/generated/survival-km.R` 可读、含 `library(survival)`/`read.table`/`plot`；DB 多一行 Script 且 `standalone_meta` 含完整契约；第二次调用复用不重写；Rscript parse 过（若有 R）。

### P4：上传 → 生成 → 执行 → 结果（闭环）
- 接 `confirm_upload`（B 任务的 required_files 来自 data_requirements）；上传后触发 `generate` → staging → qsub（或模拟）→ 日志轮询 → 结果/脚本下载消息。
- **验证**：端到端（前端登录→"生存分析"→清单→上传→见生成脚本+执行提交+日志）；无 R 环境时如实停在"脚本已生成"并标注。

### P5（可选）：富清单 UI
- 新增消息类型 `standalone_checklist` + 前端卡片（show.tsx）：必需/可选 tag、列说明、参数下拉、示例文件下载。**注意**：前端 `npm run build` 有 ~13 个预存 TS 错误（见记忆 `frontend-build-preexisting-tsc-errors`），P5 用 `npm run dev`(esbuild) 开发验证；新增组件加 `@ts-nocheck` 或确保不引入新 TS 错误。

> 首版可停在 P4（闭环跑通、可演示、脚本可下载）。P5 视前端排期。

---

## 6. 关键不变式 / 风险 / 决策点

| 项 | 说明 |
|---|---|
| 形态判定保守 | 拿不准 → multi（老路有 ToolGenesis 兜底）。避免把多步任务误判成单步、生成一个跑不通的"伪单脚本"。 |
| 不污染稳定路径 | IntentAgent/planner/orchestrator/ToolGenesis **零改动**。B 是旁路。 |
| 不伪造结果 | 无 R/SGE 环境时如实停在"脚本已生成"，提供下载，不静默编造图表。 |
| 清单精度 | `data_requirements.columns/format` 必须精确（客户清单的核心价值）；prompt 强约束 + 抽查。 |
| 幂等归档 | 同 analysis_type 第二次复用模板，不重写 .sh / 不新增 Script 行。 |
| 召回准确率 | 假阴（漏召回）→ 重新生成，harmless，靠 analysis_type 去重防堆积；假阳（错配）→ 用错模板。缓解：召回 LLM 只在高置信同义匹配时返回 slug，拿不准返回 null（§4.6）。 |
| 多次 LLM 调用 | B 闭环：classify_form + understand + generate ≈ 3 次（understand 与清单合并为 1 次）。可接受。 |
| 5 个示例不预置 | B 当场生成，跑通后归档成模板。示例是演示案例，不是待实现工具。 |

**待用户拍板（非阻塞，先按推荐做）**：
- B 归档落哪个域：推荐复用 stats 域(id=7)，或新建"独立分析"域。落盘推荐 `scripts/standalone/generated/`。
- v1 是否接受"清单走 markdown 文本气泡 + 既有上传面板"（零前端改动、快），富 UI 留 v2。推荐：是。

---

## 7. 不做（Non-goals）

- **多步独立工作流**：B 只做单步。需要复杂工作流的走老路/ToolGenesis。
- **改动 IntentAgent/planner/orchestrator/ToolGenesis**：B 是旁路，不动它们。
- **真实 R 执行环境搭建**：SGE/R/各 R 包的部署是 deferred（同 amplicon）。B 只保证"脚本生成+归档+staging"，真实出图待环境。
- **向量/embedding 检索**：模板基数小（几十种），§4.6 的 LLM retrieve-then-judge 已足够；等模板过百再考虑向量库。
- **RBAC/生成权限**：已知占位（见记忆 `known-placeholder-features`），不在本计划。
- **SGE→env 外部化**：deferred，不动。

---

## 8. 环境约束与既有计划关系（开工前必读）

- **跑后端**：`cd bioinformatics-backend && ".venv/Scripts/python.exe" -m uvicorn main:app --reload --port 8000`（**不要**用全局 uvicorn，Python 3.14 缺 passlib/bcrypt）。改大批代码后 `--reload` 偶尔卡死，kill 重启并杀孤立 reload 子进程。见记忆 `backend-venv-startup`。
- **查 .env**：先 `from dotenv import load_dotenv; load_dotenv()` 再 import config（裸 import 会误报空）。`DASHSCOPE_API_KEY` 已配(len=35)。见记忆 `check-env-via-load-dotenv`。
- **中文日志**：Windows 控制台 cp1252 / 服务器 LANG=C 会 UnicodeEncodeError；本机调试设 `PYTHONUTF8=1`。
- **无测试框架**：每阶段用一次性 Python 脚本直调服务层（放 `scripts/uploaded/`，gitignore）+ 后端日志 + 前端手点验证。
- **前端**：`npm run dev`(esbuild)；`npm run build` 有预存 TS 错误（仅 P5 受影响）。`npm install` 走 `.proxy/npm_proxy.py`。见相关记忆。
- **curl 测 API 会 mangling 中文**：用 httpx（PYTHONUTF8=1）测。
- **执行是模拟的/SGE deferred**：B 的真实执行与 amplicon 同约束，别当 bug 报。见记忆 `execution-sim-and-logging-design`。
- **已知占位**（RBAC/JWT/admin 任务列表/admin 反馈/new.tsx）：审计别当 bug。见记忆 `known-placeholder-features`。
- **提交**：仅当用户要求时 commit/push；commit 尾注 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`。

---

## 9. 推荐执行顺序

**P1 → P2 → P3 → P4**（每阶段独立验证、独立提交）；P5 可选。

- P1+P2：路由分叉 + 智能清单（无需生成脚本即可演示"像专家一样追问 + 给数据清单"）。
- P3+P4：生成 + 归档 + 执行闭环（演示"现场生成代码解决"）。
- P5：富 UI 抛光。
