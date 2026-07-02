# 意图识别与领域分流 —— 改造实现计划

> 本文件为**上下文压缩后自助执行**而写,自包含。涵盖 7 个任务(T1–T7),按"先让分类器有数据 → 再改分类器逻辑 → 最后抛光"排序。
> 仓库:Monorepo。后端 `bioinformatics-backend/`(FastAPI,Laravel 式分层),前端 `bioinformatics-frontend/`(React19+TS+Vite)。
> 仅 amplicon 一个真实领域(种子),其余是测试垃圾库。

## 0. 必读:环境与现状(开工前先看)

- **跑后端**:`cd bioinformatics-backend && ".venv/Scripts/python.exe" -m uvicorn main:app --reload --port 8000`。**不要**用全局 `uvicorn`(系统 Python 3.14 缺 passlib/bcrypt)。改完大批代码后 `--reload` 偶尔卡死,kill 重启(注意杀掉孤立的 reload 子进程)。详见记忆 `backend-venv-startup`。
- **跑前端**:`cd bioinformatics-frontend && npm run dev`(端口 5173)。`npm install` 在本机被网络策略挡,要走 `.proxy/npm_proxy.py`;`npm run dev` 不需要。详见记忆 `npm-install-via-python-proxy`。
- **前端构建**:`npm run build` 长期失败于 ~13 个预存 TS 错误(`show.tsx`),与本计划无关。开发用 `npm run dev`(esbuild)。多个 admin 页是 `@ts-nocheck`。详见记忆 `frontend-build-preexisting-tsc-errors`。
- **查 env 配置**:`.env` 由 `main.py:4 load_dotenv()` 在启动时载入;`config/*.py` 用 `os.getenv`。**裸 `python -c "from config.llm import X"` 会误报空**(不走 main.py)。正确:先 `from dotenv import load_dotenv; load_dotenv()`。详见记忆 `check-env-via-load-dotenv`。
- **`DASHSCOPE_API_KEY` 已配(len=35),LLM 子系统可用**(解析/分类/codegen 都通)。
- **无测试框架**。验证靠:服务日志 + 直接打 API + DB 查询 + 前端手点。
- **已完成(不在本计划)**:`confirm_upload`/`start_execution` 的"生成失败明显提示"修复(`chat_service.py`,已 commit 待提交)。注释:生成失败时消息文案显示 ❌ + 拒绝执行,前端 toast 报错。
- **独立轨道(不在本计划,别忘)**:per-sample 编排泛化重构(计划在 `C:\Users\henry\.claude\plans\cuddly-inventing-frog.md`,暂停);SGE 调度参数迁 env(用户说先记着别急)。

## 1. 背景与问题陈述

用户一句话进来后,系统应:① 判断是否为有效生信任务;② 判断属于哪个领域(脚本库);③ 该领域内解析意图(有什么数据/想要什么结果);④ 缺信息则追问,齐了则规划。当前实现的缺陷:

1. **无有效性闸**:"今天天气好不好"会被**建成任务、钉到 amplicon、然后被追问"你有什么数据"**。从来没有"这不是生信任务"的出口。
2. **单库短路掩盖一切**:`DomainClassifier.classify` 在启用领域=1 时**直接返回该领域,跳过所有判定**(domain_classifier.py:36-37)。用户看不出"系统怎么定领域"——因为根本没定。
3. **领域描述数据缺失**:分类器 `_classify_llm`(domain_classifier.py:60-68)确实把每个库的 `description`/`keywords` 拼进 prompt,但:① 前端**没有"新建库"表单**(`apis/domain.ts:25 CREATE_DOMAIN` 定义了却从未被调用);② 文件夹导入 `upload_library` **完全不碰** `domain.description/keywords`,只给每个 Script 从 `.md` 解析描述。结果:DB 里测试库 `测试bulk`/`新的某个领域` 的 description/keywords **都是空**,分类器只能看个名字瞎猜。
4. **顺序错 + 永久钉**:`chat()` 先建任务→先钉领域(首条消息钉死、多轮不重判)→再解析。垃圾输入被永久错误归类。
5. **解析器 `confidence` 被忽略**:`_route_decision`(chat_service.py:202)只看 available/goals 是否为空,低置信度也直接进规划器。
6. **有效性逻辑散落**:"无关则空 goals"的指令在 amplicon 硬编码 prompt(llm_parser.py:42-47)和 `build_system_prompt`(llm_parser.py:262)各写一份,不一致。

## 2. 当前代码地图(改造涉及点)

| 文件 | 关键位置 | 作用 |
|------|---------|------|
| `app/services/domain_classifier.py` | `classify` 28-52;短路 36-37;关键词 40-49;`_classify_llm` 54-92(prompt 60-68,code 匹配 86);`_fallback` 94-97 | 领域判定(本计划核心改造) |
| `app/services/chat_service.py` | `chat` 287-408;建任务 302;钉领域 348-357;解析 360-366;`_route_decision` 202-284(CASE A 208-214/B 217-233/C 236-251/D 253-284/无路径 256-266) | 聊天主流程 |
| `app/services/domain_service.py` | `create_domain` 183-211;`get_type_vocab` 98-105 | 领域 CRUD |
| `app/services/script_service.py` | `upload_library` 332-483(parse_md 432;Script 建 455-473;invalidate 476-477) | 文件夹导入(T1 落点) |
| `app/services/md_script_parser.py` | `parse_md` 189-249(找 `## 基本信息` 205;抽 description 209) | 确定性 .md 解析(已抽好字段,T1 直接复用) |
| `pkg/amplicon/llm_parser.py` | `SYSTEM_PROMPT` 37-149(有效性 42-47);`build_system_prompt` 238-268(有效性 262);`parse_natural_language` 271-326 | LLM 意图解析 |
| `app/services/parser_service.py` | `parse` 17-43;`generate_clarification` 45-58 | 解析入口 + 追问文案 |
| `app/http/requests/domain_request.py` | `CreateDomainRequest` 16-23(description/keywords **可选** 19-20) | 建领域校验 |
| `app/models/domain.py` | 字段 16-22(name/code/description/is_active/keywords/script_root/sort_order) | 领域模型 |
| `bioinformatics-frontend/src/apis/domain.ts` | `CREATE_DOMAIN` 25-27(**从未被调用**);其它 CRUD 齐全 | 前端 API |
| DB `domains` 表 | id=1 amplicon(description 57/keywords 46,种子);id=2 inactive;id=3/4 `test-rna-3b` 重复;id=5/6 空 description/keywords | 当前数据 |

---

## T1 — 导入时 LLM 自动生成库描述(数据层,优先做)

> **状态:✅ 已完成(2026-06-23)**。新建 `app/services/library_summary.py`(`summarize_library`,LLM 优先+确定性回退,CAP=80 按分类 rollup,顺带产 `example_queries` 备 T4);`upload_library` 循环内收集 `metas`,invalidate 前 fill-if-empty 回写 `domain.description`/`keywords`(不覆盖手工值,try/except 不拖垮导入)。验证:py_compile 通过、key len=35、harness 跑通 LLM/rollup(120→7行)/回退三路径。端到端导入待 T2 清理后手测。

**目标**:文件夹导入一个库后,自动用 LLM 给 `domain.description`/`keywords` 填上"这个库是干什么的",让分类器有料。

**落点**:`ScriptService.upload_library`(script_service.py:332-483)。

**为什么零额外解析**:`parse_md`(md_script_parser.py:189)已经按 `## 基本信息` 分隔符抽出了每个脚本的 `name`/`description`/`inputs`/`outputs`/`category`。`upload_library` 循环里已经调过它(line 432 `meta`),直接聚合即可,**绝不把 .md 全文喂 LLM**(解决上下文长度)。

### 实现步骤

1. **在 `upload_library` 循环里收集 meta**(script_service.py:409-474 之间)。每个成功 `created` 的脚本,append:
   ```python
   metas.append({"name": meta.get("name") or base,
                 "description": (meta.get("description") or "").strip(),
                 "category": cat,
                 "tool_id": tool_id})
   ```
   (这些变量循环里都有,零额外查询。)

2. **新模块** `app/services/library_summary.py`(纯函数,不碰 DB):
   ```python
   def summarize_library(metas: list[dict], domain_name: str) -> dict:
       """返回 {"description": str, "keywords": str}。LLM 优先,失败走确定性回退。"""
   ```
   - **构造紧凑清单**(不是 .md 全文):
     ```python
     CAP = 80
     entries = [f"- {m['name']}（分类:{m['category']}）：{m['description'][:120]}"
                for m in metas if m['name']]
     if len(entries) > CAP:
         # 大库兜底:按 category rollup,每类 count + 最多 5 个代表名 + 合并描述片段
         entries = _rollup_by_category(metas)   # 几行,而非 N 行
     ```
   - **LLM 调用**(key 已配):一次 httpx POST,DashScope,temperature 0.3,`response_format json_object`。SYSTEM:
     > 你是生物信息脚本库的画像生成器。下面是一个分析脚本库里全部脚本的清单(名称、分类、描述)。输出 JSON:`description`(1-2 句概括这个库整体做什么:属于哪个生信领域、覆盖哪些分析类型、典型流程,面向"用户描述任务时能据此判断该归入哪个库")、`keywords`(约 10 个逗号分隔,必须是用户描述任务时真正会用的术语,中文为主,可含 16S/ASV/RNA-seq 等缩写)。只输出 JSON。
     USER = 紧凑清单。解析 JSON → 返回。
   - **确定性回退**(LLM 没配/超时/解析失败,导入永不因此失败):
     ```python
     cats = sorted({m['category'] for m in metas if m['category']})
     names = [m['name'] for m in metas[:10] if m['name']]
     description = f"本库包含 {len(metas)} 个脚本，覆盖：{'、'.join(cats)}。"
     keywords = ",".join(_slug_of(n) for n in names)  # 从脚本名抽词
     ```
   - **可选加成**(喂给 T4 few-shot,一次调用两用):同一次 LLM 调用让它再吐 `example_queries`(2 条"用户会怎么问这个库"),返回里带上。

3. **回写**(`upload_library` 末尾,`invalidate` 之前):
   ```python
   if domain and metas:
       if not (domain.description or "").strip():   # 填空不覆盖手工值
           summ = summarize_library(metas, domain.name)
           domain.description = summ["description"]
           domain.keywords = summ["keywords"]
           domain.save(db)
           logger.info(f"[upload_library] 自动填充领域描述: {domain.code}")
       # 可选:顺带存 example_queries 到新字段(见 T4)
   ```

### 验证
- T2 清理后,新建一个测试库 → 导入一个文件夹 → `select code,description,keywords from domains` 确认非空且合理。
- 改 `_classify_llm` 临时把 system prompt 打 log,确认新描述进 prompt。
- 临时把 `DASHSCOPE_API_KEY` 置空(或断网)再导一次,确认走确定性回退、不报错。

### 风险
- 别覆盖手工描述(fill-if-empty)。后续可加"重新生成"admin 按钮。
- 大库 rollup 单测:_rollup_by_category 输入 200 条,确认输出行数受控。
- `category` 可能为空字符串,聚合时容错。

---

## T2 — 数据清理(独立,几分钟)

> **状态:✅ 已满足(2026-06-23),无需变更**。核查发现 id=2–6 的测试垃圾库**已被软删**(deleted_at≠0),`Domain.where()` 自动过滤,分类器视角(`where is_active=1`)只剩 id=1 amplicon(描述 57 字/关键词 46 字,种子完整),无重复 code,软删行不会泄露。T2 目标状态已达成,故未做任何 DB 写入。

**目标**:删/停 DB 里的测试垃圾库,避免干扰分类。当前 6 个 domain:id=1 amplicon(留)、id=2 inactive、id=3/4 `test-rna-3b`(重复 code)、id=5 `测试bulk`(空)、id=6 `analysis`(空)。

### 做法(任选)
- **推荐 admin UI / API**(软删 + 级联):`DELETE /api/domains/{id}`(RequireAdmin)。停用而不删用 `PATCH /api/domains/{id}/toggle`。
- **直接 SQL**:`UPDATE domains SET is_active=0 WHERE id IN (2,4,5,6);`(id=3 可留作"第二个有内容的库"以便测 T3/T4 多库分类,但其 description 也只有 5 字——建议用 T1 重新导入一个真文件夹来当第二个库)。

### 建议处置
- 删 id=2(inactive 垃圾)、id=4(重复 code)。
- 停用 id=5、id=6(空描述)。
- 测多库分类时:**导入一个真文件夹**建第 2 个库(由 T1 自动填描述),而非用 test-rna。

### 验证
`select id,code,is_active,length(description) from domains where is_active=1` → 只剩 amplicon(+ 之后 T1 建的真库),无重复 code。

---

## T3 — P0+P1:有效性闸 + 修单库短路(核心,依赖 T1)

> **状态:✅ 已完成(2026-06-23)**。`domain_classifier.py` 重写:`classify_with_relevance` 返回 `{domain_id,in_scope,confidence,reason}`;`_keyword_unique_hit` 快路径 + `_relevance_llm`(单库也验相关性,无key/失败→uncertain);删 `_classify_llm`/`_fallback`,`classify` 降薄封装。`chat()` 用 `classify_with_relevance` 替代 classify+force-amplicon:in_scope 才钉领域并解析/路由,high→`_out_of_scope_response`,medium/low/uncertain→`_uncertain_response`,不钉时 `task.domain_id` 保持 NULL。验证:5 用例全过(16S→high命中/模糊→low/天气·闲聊·你好→high拒绝),断key→天气 uncertain 走追问、16S 仍关键词命中;后端 200;无遗留旧引用。

**目标**:钉领域之前先判"是不是生信任务";即使只有一个库也跑相关性,不再无条件钦定。

### 现状缺陷
- `classify`(domain_classifier.py:36-37)单库直接返回,跳过一切。
- `classify` 永远返回 domain id(0 启用领域时 `chat` 还强行赋 amplicon,chat_service.py:353-354)。
- 无 out_of_scope 出口;`chat()` 无条件建任务 + 首条钉死领域。

### 实现步骤

1. **新增相关性判定**(domain_classifier.py,新方法):
   ```python
   @staticmethod
   def classify_with_relevance(db, content) -> dict:
       """返回 {domain_id: int|None, in_scope: bool, confidence: str, reason: str}。
       即使单库也判 in_scope。"""
       domains = 启用领域
       if not domains:
           return {"domain_id": None, "in_scope": False, "confidence": "low", "reason": "无启用领域"}
       # 快路径:唯一关键词高分命中 → 高置信直接命中
       hit = DomainClassifier._keyword_unique_hit(domains, content)  # 抽出现有 40-49 逻辑
       if hit:
           return {"domain_id": hit.id, "in_scope": True, "confidence": "high", "reason": "关键词命中"}
       # LLM 相关性判定(描述由 T1 填充)
       return DomainClassifier._relevance_llm(domains, content)
   ```
   - **`_relevance_llm`**:prompt 把每个库 `code/name/description/keywords` 列出(同现 `_classify_llm` 60-68),问:"这段输入是否属于下列任一领域?输出 JSON `{domain_code|none, confidence: high|medium|low, reason}`"。temperature 0。返回映射回 domain_id;`none` → `in_scope=False`。
   - **单库语义**:也跑 `_relevance_llm`(只有一个候选),LLM 说属于→in_scope;说 none→out_of_scope。短路不再是"无条件钦定",而是"唯一候选时仍验相关性"。
   - **无 key 兜底**:无法 LLM 判 → 关键词没命中 → `in_scope=uncertain`(返回 medium/low,**不要硬拒**)。chat 侧对 uncertain 走"追问确认"而非直接拒绝。

2. **`classify()` 改为薄封装**,返回新结构(保留旧 int 返回的调用方需适配;目前只有 chat_service.py:352 一处)。

3. **改 `chat()`**(chat_service.py:348-357):
   ```python
   verdict = DomainClassifier.classify_with_relevance(db, combined_content)
   if not verdict["in_scope"] and verdict["confidence"] != "uncertain":
       # 明确 out_of_scope:不钉领域,返回友好拒绝
       return ChatService._out_of_scope_response(task, verdict)  # 新助手消息 type=text/clarification
   if verdict["in_scope"]:
       task.domain_id = verdict["domain_id"]; task.save(db)
   else:
       # uncertain:不钉,让下一轮再判(衔接 T5)
       pass
   domain_id = task.domain_id  # 可能 None → 解析/规划需处理
   ```

4. **新增 `_out_of_scope_response`**(chat_service.py):返回一条消息,内容如"这看起来不是生物信息分析任务。我可以帮你做扩增子/微生物群落分析(物种注释、多样性、差异分析等),请描述你的数据和目标。" **不钉领域**。可复用 `type="clarification"`(前端按 RichTextContent 渲染 content,无需新前端)。

5. **修掉"0 启用领域强行赋 amplicon"**(chat_service.py:353-354):无启用领域时也走 out_of_scope,而不是硬塞 amplicon。

### 验证
- "今天天气好不好"→ 不建/不钉任务,返回 out_of_scope 文案。查 DB 该 task 的 `domain_id` 为 NULL。
- "我想做 16S 扩增子多样性分析"→ in_scope,钉 amplicon,正常走到 _route_decision CASE D 规划。
- 单库(只 amplicon)下:天气被拒、生信问题被接纳 —— 证明短路不再跳过相关性。
- 断 key:天气问题走 uncertain → 追问,不硬拒。

### 风险
- LLM 相关性多一次调用,增延迟。关键词快路径覆盖大多数明确命中。
- 不要过度拒绝(误伤真任务)。保守:high 置信 none 才拒;medium/low 走追问。
- `domain_id=None` 时下游解析/规划要能处理(解析可继续,规划需要 domain_id → 此时先不规划,等钉了再说)。

---

## T4 — P2:分类器输出 none + 置信度 + few-shot(依赖 T3)

> **状态:✅ 已完成(2026-06-23)**。`domains` 加 `examples`(TEXT,JSON list)字段 + `migrate_domains_v3` 增量迁移(已跑,列已加)。`upload_library` 回写时一并存 `example_queries`。`_relevance_llm` prompt 每库附 examples(1-2 条)作 few-shot,返回结构增 `candidates`(映射真实领域、去重、主选居首);新增 `_map_candidates`/`_ensure_first`/`_parse_examples` 辅助。`chat()`:in_scope 但 medium/low 且 candidates≥2 时不钉领域,改 `_disambiguate_response` 列候选请确认。验证:examples 列可读(amplicon 现空,待 T1 导入填)、candidates 正确返回、`_disambiguate_response` 渲染正确、单库不受影响、后端 200。观察:LLM 多返回单个候选,故 ≥2 消歧是安全网(真跨领域才触发),符合"避免每次都追问"。

**目标**:多库低置信时追问"你是指 A 还是 B?",而非闷头猜。

### 实现步骤
1. T3 的 `_relevance_llm` 已返回 `confidence`/`reason`。
2. **few-shot**:T1 的 `summarize_library` 顺带产 `example_queries`。新增 Domain 字段 `examples`(TEXT, JSON list)—— 加 model 字段 + `migrate` 增量(`migrate_seed.py` 里有先例)。T1 回写时一并存。`_relevance_llm` prompt 里每个库附 1-2 条 example。
3. **低置信多库处理**(chat_service.py):verdict confidence=medium/low 且 in_scope 但 domain 不唯一时 → 返回一条"我猜可能是 A 或 B,能确认吗?"的追问(复用 clarification),列出候选库的 description,**不钉领域**(下一轮再判)。

### 验证
- 两个有描述的库,问一个模糊问题 → 返回候选追问而非直接规划。
- example_queries 进 prompt(log 验证)。

### 风险
- 加 DB 字段要写增量 migration(`migrate_seed.py` 末尾仿 `migrate_messages_v2`)。
- 低置信阈值要调,避免每次都追问。

---

## T5 — P3:延迟钉领域 / 早期允许重判(T3 已部分启用)

> **状态:✅ 已完成(2026-06-23)**。`chat()` 闸块改三分支:① 路径已确认(`_path_confirmed` 查 `select_path` 消息,免加字段)→ 锁定不重判;② 已钉未确认→`classify_with_relevance` 重判,若 in_scope 且指向**别的**领域(high/medium)则切换 `task.domain_id` 并清空 `history_dicts`(避免旧领域污染);③ 首次→相关性闸(T3/T4)。off-topic/uncertain(verdict_domain=None)不取消已钉领域,任务保持原领域正常解析。验证:`_path_confirmed` 真实任务区分正确(task13 未锁/task26 锁定);单库重判不变性(已钉 amplicon 任务任何问法 switch 恒 False);后端 200。多库切换待第 2 个库导入后实测。

**目标**:别首条永久钉死;允许早期(未确认路径前)重判。

### 实现步骤
- T3 已经"未确认 in_scope 不钉"。
- 补:**已钉但用户改口**的处理——若 `task` 还没确认过路径(没有 `confirm_path` 产生的 message),且当前轮关键词/LLM 明确指向**另一个**领域 → 允许重判换领域。
- 锁定条件:一旦 `confirm_path` 跑过(workflow_candidates 已选)→ `task.domain_locked=1`,后续不再重判。可加 `domain_locked` 布尔字段,或用"是否存在已确认路径消息"推断(免加字段)。

### 验证
- 第一句"做 RNA-seq"→ 钉 A;第二句"不对我说的是扩增子"→ 早期换回 amplicon。
- 确认路径后再改口 → 不换。

### 风险
- 重判可能丢失上一轮解析的状态;重判时清空 `available_inputs`/`goal_types` 缓存。

---

## T6 — P4:把解析器 confidence 用进路由(独立,小)

> **状态:✅ 已完成(2026-06-23)**。`_route_decision` 加 `confidence` 参数(默认 medium);CASE D(输入/目标都有)前,`confidence=="low"` → 返回追问确认、不直接进规划器;medium/high 放行。caller 传 `parser_result.get("confidence","medium")`。验证:low+双齐 → clarification 不规划;medium → 越过闸进规划器;后端 200。

**目标**:`_route_decision` 不再无视 `confidence`。

### 实现步骤
- `_route_decision` 签名加 `confidence`(chat_service.py:369 调用处传入 `parser_result["confidence"]`)。
- CASE D(都有、要规划)前加判断:`if confidence == "low":` → 返回追问"我理解你想做 {goals},但不太确定,能再说细一点吗?"(复用 clarification),**不直接进规划器**。
- medium 可放行(或加一句"如果理解有误请纠正")。

### 验证
- 构造低置信解析(模糊输入)→ 不直接规划,先追问。

### 风险
- 别把 medium 也拦了,否则老追问很烦。

---

## T7 — P5:统一有效性逻辑(依赖 T3)

> **状态:✅ 已完成(2026-06-23)**。`llm_parser.py` 收拢:T3 闸已接管有效性(且确认 `ParserService.parse` 仅在 chat() 过闸后调用,out-of-scope 到不了解析器),故删 SYSTEM_PROMPT 的"⚠️输入有效性判断"段 + 末尾"无关→空 goals"提醒;删 build_system_prompt 的"无关→空 goals"行;两 prompt 加"输入已由上游确认属于本领域"注。confidence low 重框为"数据/目标提取不清晰"(保留 T6 用)。验证:grep 确认有效性短语全清;回归 3 个清晰生信问法抽取不变(双端16S→TAXONOMY+ALPHA / DADA2后→LEFSe / PCoA+聚类→PCOA_PLOT+UPGMA);后端 200。

**目标**:T3 接管有效性后,清掉散落重复的指令。

### 实现步骤
- 删/简化 `SYSTEM_PROMPT` 里"输入与生信无关则 goal_types=[]"那段(llm_parser.py:42-47)——有效性已由 T3 闸处理,到达解析器的都已是 in_scope。
- 同理简化 `build_system_prompt`(llm_parser.py:262)那句。
- 解析器专注抽 inputs/goals。

### 验证
- 回归:正常生信问题解析结果不变;天气问题在 T3 闸就被挡,不到解析器。

### 风险
- 确认 T3 闸对所有入口生效(图片输入路径 chat_service.py:319-328 也要先过闸)。

---

## 3. 推荐执行顺序

1. **T2**(数据清理,几分钟,先清干净)
2. **T1**(自动描述,数据层基础)
3. **T3**(有效性闸 + 修短路,核心;需 T1 的描述)
4. **T4**(none+置信度+few-shot,需 T3)
5. **T5**(延迟钉/重判,T3 已铺路)
6. **T6**(confidence 进路由,独立小改)
7. **T7**(收拢重复逻辑,需 T3)

每步做完:服务日志确认 + DB 查询 + 前端手点回归。无测试框架,改一处验一处。

## 4. 关键不变式(别破坏)

- `DomainService._tools_cache` 是唯一缓存,脚本写操作必须 `invalidate(domain_id)`(T1 改 upload_library 别忘,已有 line 476-477)。详见记忆 `multi-domain-script-refactor`。
- 解析在领域分流**之后**(类型 ID 领域专属)。T3 改顺序时保持。
- amplicon 领域用详细 `SYSTEM_PROMPT`(历史行为),其它领域用 `build_system_prompt`。T7 简化时两者同步。
- 生成失败提示修复已上线:`confirm_upload` 失败写 status/errors 不写脚本桩;`start_execution` 拦截 failed 状态。T3/T4 改 chat 流程时别回退这点。

## 5. 涉及新建文件/字段汇总

- 新文件:`app/services/library_summary.py`(T1)。
- 新字段(可选,T4):`domains.examples`(TEXT,JSON list)+ 增量 migration。
- 新字段(可选,T5):`tasks.domain_locked`(BOOL)或用推断免加。
