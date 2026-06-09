# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Activate venv first — system python is a Windows Store placeholder
.venv/Scripts/activate        # Git Bash on Windows

# Install dependencies
pip install -r requirements.txt

# Create/update database tables + seed data
python migrate_seed.py

# Drop and recreate all tables (development only)
python migrate_seed.py --fresh

# Start development server
uvicorn main:app --reload
```

No test framework is configured.

## Architecture

FastAPI bioinformatics backend with **Laravel-style layered architecture**:

```
HTTP Request → Route (routes/) → Controller (app/http/controllers/) → Service (app/services/) → Model (app/models/) → Database
                                    ↓
                              Pydantic Request (app/http/requests/) for validation
```

All routes mount under `/api` via `routes/api.py`. Static file serving at `/uploads` for uploaded files (`main.py`).

### Model Base Class

All models inherit from `Model` (`app/models/model.py`), which provides:
- Automatic timestamps (`created_at`, `updated_at`)
- Soft delete (`deleted_at` is an **Integer** timestamp, default `0`, not `NULL`)
- Laravel-like methods: `find()`, `all()`, `where()`, `with_trashed()`, `only_trashed()`, `save()`, `delete()`, `force_delete()`, `restore()`

**Field conventions:** All columns must specify `nullable` and a `default`. Required fields use `nullable=False` with type-appropriate defaults (`''` for String/Text, `0` for Integer). Foreign keys use `nullable=False, default=0`.

**Column ordering:** Concrete models redeclare `id`, `created_at`, `updated_at`, `deleted_at` to ensure defined column order in SQLite.

**Serialization:** Models override `to_dict()` for custom output (e.g., `User.to_dict()` hides `hashed_password`, includes `roles`/`permissions`; DateTime fields formatted via `.isoformat()`).

### Domain Model Relationships

```
User
├── projects (Project.user_id) ─── tasks (Task.project_id) ─── messages (Message.task_id)
├── tasks (Task.user_id)
├── templates (Template.user_id)
└── roles (M2M via UserRole) ─── permissions (M2M via RolePermission)
```

Script system: `ScriptFolder` (tree, `parent_id`) → `Script` (tools with `tool_id`, `inputs`, `outputs`, `file_path`).

### RBAC

- `user_roles` — User ↔ Role (M2M)
- `role_permissions` — Role ↔ Permission (M2M)
- `User.to_dict()` automatically includes roles and deduplicated permissions
- Seed: `admin` gets all permissions; `user` gets create+read on projects/tasks/messages

### Authentication

JWT via `python-jose` + `passlib`. Protected routes use `current_user: User = Auth`:

```python
from app.http.middleware import Auth

@router.get("/protected")
def protected_route(current_user: User = Auth):
    return current_user.to_dict()
```

Login returns `{"token": "...", "user": {...}}` (field name is `token`, not `access_token`). Token expiry is 7 days.

## Chat & Analysis Pipeline

The core feature is an LLM-driven bioinformatics analysis assistant. The full interaction flow:

1. **User sends message** → `ChatService.chat()` creates/updates Task + Message
2. **Parse intent** → `ParserService.parse()` (LLM first via `llm_parser.py`, keyword fallback via `nl_parser.py`) extracts `available_inputs` + `goal_types`
3. **Route decision** → Based on what's known (inputs, goals, both, neither):
   - Neither → clarification prompt
   - Only inputs → ask for goals
   - Only goals → ask for data type
   - Both → run planner
4. **Plan workflow** → `PlannerService` calls BFS planner (`pkg/amplicon/planner.py`) to find tool chains
5. **User confirms path** → `ChatService.confirm_path()` generates execution code via LLM, identifies required files
6. **User uploads files** → `ChatService.confirm_upload()` validates extensions against `required_files`
7. **Execute** → `ChatService.start_execution()` writes script to `SHARED_DIR`, runs `docker exec sge-master qsub` for SGE job submission
8. **Monitor** → `ChatService.get_execution_logs()` reads SGE log from `SHARED_DIR`

Message types: `"text"`, `"clarification"`, `"workflow"`, `"path"`, `"code"`, `"file_request"`.

### Amplicon Tool System (`pkg/amplicon/`)

The analysis pipeline is built around a tool registry where each tool maps **input data types → output data types**:

- **`amplicon_tools.py`** — `ToolDef` registry (`get_all_tools()`), data type name mappings (`DATA_TYPE_NAMES`), file requirement definitions (`DATA_TYPE_TO_FILE_REQUIREMENT`), and `resolve_root_inputs()` to derive user-required uploads from a tool chain
- **`planner.py`** — Two-phase BFS planner: Phase 1 finds core paths to intermediate states, Phase 2 attaches terminal tools. Returns up to `top_n` `WorkflowCandidate`s
- **`nl_parser.py`** — Keyword-based fallback parser (Chinese + English keywords)
- **`llm_parser.py`** — LLM-based parser using DashScope, includes `SYSTEM_PROMPT` (structured JSON parsing) and `CLARIFICATION_SYSTEM_PROMPT` (friendly follow-up questions)
- **`code_templates.py`** — Shell script templates per tool ID and `generate_workflow_script()` for fallback code generation

Tool IDs follow `amp-{short-name}` pattern (e.g., `amp-dada2`, `amp-lefse`, `amp-pca`). Categories: 数据预处理, 质量控制, 核心分析, 多样性分析, 统计检验, 可视化, 排序分析, 功能预测.

Seed data (`migrate_seed.py`) auto-populates `Script` records from `get_all_tools()`, mapping each tool to its shell script in `scripts/Amplicon/`.

### Script Code Generation

When a user confirms an analysis path, `ChatService._generate_script_with_llm()` sends the tool chain's original script contents to the LLM with instructions to produce a single concatenated bash script with correct parameter passing. Falls back to simple concatenation if LLM fails. Scripts target a Docker container with SGE, using `/shared/` as the base directory.

## Configuration

| File | Purpose |
|------|---------|
| `config/app.py` | App name, version |
| `config/database.py` | SQLAlchemy + SQLite (`bioflow.db`) |
| `config/auth.py` | JWT secret, token expiry |
| `config/llm.py` | DashScope API key, base URL, model name, parser/codegen timeouts |
| `config/upload.py` | Upload directory (`storage/uploads`), max size, allowed extensions |

### Environment Variables

```
JWT_SECRET_KEY=...
DATABASE_URL=sqlite:///./bioflow.db
DASHSCOPE_API_KEY=...
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL_NAME=qwen-plus
DASHSCOPE_VL_MODEL=qwen-vl-plus          # Vision model for image analysis
LLM_PARSER_TIMEOUT=30                     # seconds
LLM_CODEGEN_TIMEOUT=120                   # seconds (min 300 in practice)
SHARED_DIR=shared                         # Docker shared volume mount point
UPLOAD_DIR=storage/uploads
MAX_UPLOAD_SIZE_MB=50
```

## Database

SQLAlchemy ORM with SQLite. Sessions via `Depends(get_db)` or `SessionLocal()`. Tables auto-created by `migrate_seed.py`, which also runs incremental migrations (e.g., `migrate_messages_v2` adds structured columns, `migrate_tasks_v2` adds `qsub_id`/`script_path`).

## Adding New Features

1. **Model** (`app/models/`) — inherit `Model`, redeclare `id`/`created_at`/`updated_at`/`deleted_at`
2. **Service** (`app/services/`) — static methods on a class
3. **Controller** (`app/http/controllers/`) — delegates to service
4. **Request** (`app/http/requests/`) — Pydantic `BaseModel`
5. **Route** (`routes/`) — `APIRouter`, register in `routes/api.py`
6. **Migrate** — `python migrate_seed.py`

## Testing Accounts

- `admin@bioflow.com` / `admin123` — admin role, all permissions
- `user@bioflow.com` / `user123` — user role, create+read on projects/tasks/messages
