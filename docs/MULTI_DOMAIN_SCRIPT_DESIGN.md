# 多领域脚本库 + 自动建图 + 描述分流 设计文档

> 状态：设计已定稿（2026-06-16），待实施。
> 适用范围：`bioinformatics-backend/` + `bioinformatics-frontend/` 全栈改造。

---

## 1. 背景与目标

### 1.1 当前问题

现状把整个分析流水线**硬编码绑死在"扩增子（amplicon）"一个领域上**：

- 规划器 `PlannerService._get_tools()` 读取硬编码的 `get_all_tools()`（`pkg/amplicon/amplicon_tools.py:178`）
- 执行器 `orchestrator.py` 读取硬编码的 `TOOL_SCRIPT_CALLS`（`pkg/amplicon/script_registry.py:31`）
- 数据类型是全局字典 `DATA_TYPE_NAMES` / `DATA_TYPE_TO_FILE_REQUIREMENT`（`amplicon_tools.py:123` / `:21`）
- `/admin/graph` 是一个 527 个随机假节点的**纯前端原型**，无后端、保存无效（`bioinformatics-frontend/src/pages/admin/graph/index.tsx:61`）
- `/admin/scripts` 能 CRUD，但**改的是 DB，规划器不读 DB** → 上传的脚本根本跑不起来

**根因**：缺少"领域（Domain）"这一层抽象，所有领域知识写死在 Python 里，不可扩展、不可在 UI 编辑。

### 1.2 目标需求

1. **多文件上传**：脚本上传支持一次选多个文件。
2. **分领域**：不再全挤在一个"脚本库"里；按领域划分（扩增子是一个领域，还会有 RNA-Seq、WGS 等）。系统允许新建不同类的脚本库。
3. **每领域单独建图**：新建的脚本库支持多文件上传，并**单独建一个图**。
4. **领域内再分类**：每个脚本库内仍需区分"预处理 / 质量控制 / …"等用途分类（沿用现有 `ScriptFolder` 语义）。
5. **知识图谱展示全部图 + 启用开关**：图谱页能看到所有领域的图，并能选择启用 / 禁用哪些。
6. **描述分流**：用户端新建任务时，根据文字描述自动判断属于哪个领域，并用对应领域的图来规划路径。

---

## 2. 已确定的关键决策

| 决策点 | 选定方案 | 说明 |
|--------|---------|------|
| 扩增子如何处理 | **统一到 DB** | amplicon 也变成 DB 里的一个领域（种子迁移时把硬编码数据灌入），规划器/执行器统一走 DB。单一真相源、上传脚本能真正跑、UI 可编辑 amplicon。 |
| 图（DAG）如何构建 | **自动推导** | 脚本声明 inputs/outputs 类型，图自动成型（与现 amplicon 一致：A.outputs ∩ B.inputs ≠ ∅ 即一条边）。admin 只在图不对时回去改脚本 IO。 |
| 多文件上传粒度 | **每个文件 = 一个脚本/节点** | 多个脚本文件各自成为独立 `Script` 行（图上的独立节点）。 |

> 图采用**自动推导**而非手动画边：省力，且与现有已验证的规划器模型（`planner.py:64-79` 按 inputs/outputs 类型匹配遍历）完全一致。

---

## 3. 总体架构

```
admin 建领域 → 定义该领域"数据类型词表" + 上传脚本（声明 IO + CLI 调用参数）
                              │
                              ▼
              图 = 由脚本 inputs/outputs 类型匹配自动推导（DAG）
                              │
                              ▼
用户建任务（文字描述） → DomainClassifier 分流到某领域（只看 is_active=1）
                              │
                              ▼
   按该领域类型词表解析 → 用该领域工具图规划 → 用该领域脚本调用生成 bash
```

核心判断：**把硬编码下沉成数据库驱动，让"领域"成为一等公民**。没有这一步，六条需求都落不了地。

---

## 4. 数据模型设计

### 4.1 新增 `domains` 表（领域 / 脚本库）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `name` | String | 显示名，如"扩增子分析" |
| `code` | String, unique | 机器码，如 `amplicon` |
| `description` | Text | 领域描述（用于路由分类提示词） |
| `is_active` | Integer, default 1 | **图谱"启用"开关**；关闭后不参与路由 |
| `keywords` | String, default '' | 路由分流用关键词，逗号分隔 |
| `script_root` | String, default 'uploaded' | 该领域脚本在磁盘上的根目录（amplicon=`Amplicon`，新领域=`uploaded`） |
| `sort_order` | Integer, default 0 | |
| `created_at` / `updated_at` / `deleted_at` | | 沿用基类 `Model` 约定 |

### 4.2 新增 `data_types` 表（领域级类型词表）

把现在全局的 `DATA_TYPE_NAMES` + `DATA_TYPE_TO_FILE_REQUIREMENT` 拆到每个领域下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `domain_id` | FK → domains | |
| `type_id` | String | 类型 ID，如 `FASTQ_PAIR` |
| `label` | String | 中文名，如"双端测序原始数据" |
| `description` | Text | |
| `extensions` | Text(JSON) | 如 `'[".fastq.gz"]'` |
| `required` | Integer, default 1 | |
| `multiple` | Integer, default 0 | |
| `is_uploadable` | Integer, default 0 | 是否用户需上传的"根输入"（对应原 `DATA_TYPE_TO_FILE_REQUIREMENT` 那 14 个） |
| `created_at` / `updated_at` / `deleted_at` | | |

**约束**：`unique(domain_id, type_id)` —— 不同领域类型词表完全独立（amplicon 的 `FEATURE_SEQS` 与 RNA-Seq 的 `COUNTS_MATRIX` 互不相干），图天然隔离。

### 4.3 `script_folders` 改动

新增 `domain_id`（FK → domains, default 0）。

现有 `parent_id` 自引用树语义不变：领域下的"预处理/质控"就是该领域内 `parent_id=0` 的子文件夹。

### 4.4 `scripts` 改动

| 新增字段 | 类型 | 说明 |
|---------|------|------|
| `domain_id` | FK → domains | 冗余，便于按领域查询 |
| `call_params` | Text(JSON), default '' | 执行器要的 CLI 参数 |
| `call_outputs` | Text(JSON), default '' | 输出文件定义 |
| `per_sample` | Integer, default 0 | 是否逐样本处理 |

`call_params` / `call_outputs` 即把硬编码 `ScriptCallDef`（`script_registry.py:23`）下沉为 DB 字段：

```jsonc
// call_params
[
  {"flag": "-r1", "data_type": "FASTQ_R1", "required": true},
  {"flag": "-f",  "data_type": "_PRIMER_F", "required": true}
]
// call_outputs
[
  {"data_type": "TRIMMED_R1", "filename": "${sample}.cutadapt.R1.fastq.gz"}
]
```

---

## 5. 各需求落地方案

| 需求 | 落地方式 |
|------|---------|
| **1. 多文件上传** | 上传弹窗改多选（`multiple`）；后端新增 `POST /api/scripts/bulk`（multipart 多 script_file）；循环建多条 `Script` 行，每个文件 LLM 解析 IO（复用 `script_service.py:19 _parse_script_io_llm`）；前端给一个批量复核表 |
| **2. 分领域 / 新建脚本库** | 新增 `/admin/domains` 领域 CRUD；建领域时同时建它的类型词表 + 预置分类文件夹（预处理/质控…） |
| **3. 每领域单独建图** | 图 = 该领域 `verified=1 & is_active=1` 脚本的 IO 推导 DAG，领域间互不影响 |
| **4. 领域内再分类** | 沿用 `ScriptFolder` 树，只是多了 `domain_id`；分类=领域内子文件夹，UI 不变 |
| **5. 图谱展示全部 + 启用开关** | `/admin/graph` 重写：领域选择器 → 渲染选中领域推导图；每领域一个 `is_active` 开关；关闭的领域不参与路由 |
| **6. 描述分流** | 新增 `DomainClassifier`（LLM 主 + 关键词备），插在解析之前 |

---

## 6. 后端改造（按链路顺序）

### 6.1 领域路由（新增，期三）

`chat_service.py` 现在在 `:158` 直接拿 `available_inputs/goals` → `:208 plan_workflow`。改造后顺序：

```
1. domain_id = DomainClassifier.classify(db, content)      # 只看 is_active=1 的领域
2. types     = DataType.for_domain(db, domain_id)
3. parsed    = ParserService.parse(content, types)         # 解析器注入该领域词表
4. candidates= PlannerService.plan_workflow(db, domain_id, available, goals)
5. code      = generate_orchestrator_script(db, domain_id, tool_ids, ...)
```

> **关键约束：解析必须在分流之后**——`available_inputs`/`goal_types` 是领域相关的类型 ID，不同领域词表不同。

`DomainClassifier` 草案：

```python
class DomainClassifier:
    @staticmethod
    def classify(db, content: str) -> int | None:
        domains = Domain.where(db, is_active=1)
        # 主：LLM（喂每个领域 name/description/keywords → 返回 code）
        # 备：关键词命中 domain.keywords
        # 无命中 → 返回 None（走默认/澄清）
```

### 6.2 规划器改造（期二）

`PlannerService`（`planner_service.py:18-24`）改成按领域从 DB 构建：

```python
class PlannerService:
    _tools_cache = {}   # domain_id -> list[ToolDef]

    @classmethod
    def _get_tools_for_domain(cls, db, domain_id):
        if domain_id not in cls._tools_cache:
            rows = Script.where(db, domain_id=domain_id, verified=1, is_active=1)
            cls._tools_cache[domain_id] = [
                ToolDef(id=s.tool_id, name=s.name,
                        inputs=json.loads(s.inputs or "[]"),
                        outputs=json.loads(s.outputs or "[]"),
                        category=s.category) for s in rows
            ]
        return cls._tools_cache[domain_id]

    @staticmethod
    def plan_workflow(db, domain_id, available_inputs, goal_types):
        tools = PlannerService._get_tools_for_domain(db, domain_id)
        request = PlanningRequest(available_inputs=available_inputs, goal_types=goal_types)
        candidates = plan(tools, request)   # plan() 本身不动
        return [asdict(c) for c in candidates]
```

- `plan()`（`planner.py:32`）**不用改**——它本来就吃 `list[ToolDef]`。
- **缓存失效**：脚本上传/校验/启用/编辑/删除时清掉该 `domain_id` 的缓存。

### 6.3 `resolve_root_inputs` 改造（期二）

`amplicon_tools.py:227` 现在读全局 `DATA_TYPE_TO_FILE_REQUIREMENT`。改为领域感知：上传需求从该 domain 的 `is_uploadable=1` 类型推导。

### 6.4 执行器改造（期二，最硬的一块）

`orchestrator.py:46` 现在用 `get_script_call(tool_id)` 读硬编码。改成从 DB 读：

```python
def _build_call_def(db, domain_id, tool_id):
    s = ScriptService.get_by_tool_id(db, tool_id)   # 已有，script_service.py:88
    return ScriptCallDef(
        tool_id=tool_id,
        script_path=s.file_path,
        params=json.loads(s.call_params or "[]"),
        outputs=json.loads(s.call_outputs or "[]"),
        per_sample=bool(s.per_sample),
    )
```

> **低风险关键点**：amplicon 的 `tool_id` 仍是 `amp-*`，所以 `orchestrator.py:157-255` 的逐样本特殊分支（`amp-cutadapt`/`amp-flash`/`amp-frags-qc`/`amp-dada2`）切换后照常工作——它们只依赖 `call_def.script_path`，现在从 DB 取而已。新领域默认走通用 `_build_single_command`（`:258`，本身已数据驱动）。

`generate_orchestrator_script` 签名加 `db, domain_id` 前两个参数。

### 6.5 服务层 / 路由

- 新增 `app/services/domain_service.py`、`app/http/controllers/domain_controller.py`、`app/http/requests/domain_request.py`、`routes/domain.py`
- `routes/domain.py` 接口：
  - `GET    /api/domains/`           列表（含 is_active）
  - `POST   /api/domains/`           新建领域（含类型词表 + 预置分类文件夹）
  - `PUT    /api/domains/{id}`       编辑
  - `PATCH  /api/domains/{id}/toggle` 启用/禁用
  - `GET    /api/domains/{id}/graph` 返回该领域推导 DAG 的 JSON（节点=脚本，边=类型匹配）
- `routes/script.py`：
  - 新增 `POST /api/scripts/bulk`（多文件）
  - 现有接口增加 `domain_id` 透传
- **顺手补 RBAC**：当前脚本写接口只校验"登录"不校验 admin（`routes/script.py` 的 `Auth` 依赖太弱），本次新增 `require_admin` 依赖，脚本/领域写操作全部锁死 admin。

---

## 7. 前端改造

### 7.1 Admin 端

| 页面 | 改动 |
|------|------|
| `/admin/domains`（**新**） | 领域列表 + 新建/编辑 + `is_active` 开关 + 类型词表编辑器 |
| `/admin/scripts`（改） | 顶部加领域选择器；上传弹窗支持多文件；校验弹窗加 `call_params/call_outputs/per_sample` 编辑 |
| `/admin/graph`（**重写**） | 删除现 527 假节点的 `generateScripts`（`graph/index.tsx:61`）；改读 `/api/domains/{id}/graph`；用 **ReactFlow**（`@xyflow/react` 已装，比 `react-force-graph-2d` 更适合工具 DAG）渲染；领域切换 + 启用开关；点节点 → 编辑该脚本 IO |

### 7.2 用户端

- 建任务流程基本不变（`index.tsx` 的 `handleSend`），后端自动分流领域。
- UI **回显识别到的领域**（如"识别到领域：扩增子分析"），并允许用户手动覆盖（防 LLM 分错）。

### 7.3 前端 API 层（`src/apis/`）

- 新增 `domain.ts`：`GET_DOMAINS / CREATE_DOMAIN / UPDATE_DOMAIN / TOGGLE_DOMAIN / GET_DOMAIN_GRAPH`
- `script.ts` 新增 `BULK_UPLOAD_SCRIPTS`，现有方法加 `domainId` 参数
- `types/models.ts` 新增 `Domain`、`DataType` 接口

---

## 8. 种子迁移方案（期一）

在 `migrate_seed.py` 增量迁移（仿现有 `migrate_messages_v2` 模式）。**此期不改运行路径，旧流程照常。**

1. 建 `domains` / `data_types` 两张表
2. 种一个领域 `扩增子分析`（code=`amplicon`, script_root=`Amplicon`, keywords=`扩增子,16S,ASV,微生物群落,DADA2,…`）
3. 从 `DATA_TYPE_NAMES`（`:123`）灌 45 个类型；其中在 `DATA_TYPE_TO_FILE_REQUIREMENT`（`:21`）里的 14 个补 `extensions/required/multiple` + `is_uploadable=1`
4. 现有 8 个根 `ScriptFolder` + 36 个 `Script` 全部打上 `domain_id=amplicon`
5. 按 `tool_id` join `TOOL_SCRIPT_CALLS`（`:31`），把每个 amplicon 脚本的 `call_params/call_outputs/per_sample` 回填

**做完后 DB 是硬编码数据的完整镜像**——期二切换开关时，amplicon 行为完全不变。这是整个方案能低风险推进的支点。

---

## 9. 实施分期

每期可独立验证，amplicon 全程不挂。

| 期 | 内容 | 验收标准 |
|----|------|---------|
| **期一** | Domain/DataType 建表 + 种子迁移（amplicon 完整入 DB） | DB 有完整镜像；旧流程照常跑，回归测试通过 |
| **期二** | 规划器/执行器切到 DB（`PlannerService`/`orchestrator`/`resolve_root_inputs`） | amplicon 端到端与切换前一致（同样描述→同样路径→同样脚本） |
| **期三** | 领域 CRUD + 多文件上传 + 图谱重写 + 路由分流 | 能新建领域、传脚本、用户建任务自动走对应图 |

**推荐从期一开始**（纯加表 + 种子，零风险，且是后面两期的地基）。

---

## 10. 风险与后续工作

### 10.1 本期不阻塞、留作后续

- **逐样本（`per_sample`）逻辑通用化**：现 amplicon 的 per-sample 循环（`orchestrator.py:182-235`）是硬编码特殊分支。期二先保证 amplicon 不变、新领域走单命令；后续把 per-sample 提成"领域级配置模板"，让新领域也能多样本。
- **LLM 解析 call_params 准确度**：上传时 LLM 辅助填，以人工校验为准。
- **图的手动调边**：当前纯自动推导；若日后出现类型匹配歧义，可加显式边表覆盖（决策 2 已留口子）。

### 10.2 风险点

| 风险 | 缓解 |
|------|------|
| 期二切换后 amplicon 行为回归 | 种子迁移保证 DB 镜像完整；切换前后用同一组描述做对照测试 |
| LLM 领域分流分错 | 关键词备选 + 用户端手动覆盖 |
| DB 类型词表与脚本声明不一致导致图断裂 | 图谱页可视化断裂，admin 能一眼看出并修脚本 IO |
| 缓存陈旧 | 任何脚本/领域写操作都清对应 domain 缓存 |

---

## 11. 关键文件索引

### 后端
- 规划器算法：`bioinformatics-backend/pkg/amplicon/planner.py:32`（`plan()`，不改）
- 规划器服务：`bioinformatics-backend/app/services/planner_service.py:18`（改：按领域读 DB）
- 工具/类型定义：`bioinformatics-backend/pkg/amplicon/amplicon_tools.py`（`:11 ToolDef`、`:21 FILE_REQUIREMENT`、`:123 NAMES`、`:178 get_all_tools`、`:227 resolve_root_inputs`）
- 脚本调用注册表：`bioinformatics-backend/pkg/amplicon/script_registry.py:31`（`TOOL_SCRIPT_CALLS`，迁移后退役，留作种子源）
- 执行器：`bioinformatics-backend/pkg/amplicon/orchestrator.py:46`（改：从 DB 取 call_def）
- chat 主流程：`bioinformatics-backend/app/services/chat_service.py:158`（parse→plan 衔接点，插领域路由）
- Script 模型：`bioinformatics-backend/app/models/script.py`
- ScriptFolder 模型：`bioinformatics-backend/app/models/script_folder.py`
- 脚本服务：`bioinformatics-backend/app/services/script_service.py:19`（`_parse_script_io_llm`）、`:88`（`get_by_tool_id`）、`:132`（`upload_script`）
- 脚本路由：`bioinformatics-backend/routes/script.py`
- 种子：`bioinformatics-backend/migrate_seed.py`

### 前端
- 脚本管理页：`bioinformatics-frontend/src/pages/admin/scripts/index.tsx`
- 图谱页（待重写）：`bioinformatics-frontend/src/pages/admin/graph/index.tsx`
- 脚本 API：`bioinformatics-frontend/src/apis/script.ts`
- 类型定义：`bioinformatics-frontend/src/types/models.ts:37`
- 用户端任务入口：`bioinformatics-frontend/src/pages/user/index.tsx`
- 路由：`bioinformatics-frontend/src/routes/router.tsx:46-56`
- 图库依赖：`@xyflow/react`（已装，图谱重写用）、`react-force-graph-2d`（现假原型用，可弃）
