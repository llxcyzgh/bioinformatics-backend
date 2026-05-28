# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Create/update database tables (runs migrations and seeds)
python migrate_seed.py

# Drop and recreate all tables (development only)
python migrate_seed.py --fresh

# Start development server
uvicorn main:app --reload

# Alternative: run on specific host/port
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

This is a **FastAPI bioinformatics backend** following a **Laravel-style directory structure**. The architecture uses strict layering:

- **Routes** (`routes/`) - API endpoint definitions, delegate to controllers
- **Controllers** (`app/http/controllers/`) - Request handling, delegate to services
- **Services** (`app/services/`) - Business logic layer
- **Requests** (`app/http/requests/`) - Pydantic validation schemas
- **Models** (`app/models/`) - SQLAlchemy ORM with Laravel-like methods
- **Middleware** (`app/http/middleware/`) - Cross-cutting concerns (auth, etc.)

### Request Flow

```
HTTP Request → Route → Controller → Service → Model → Database
                    ↓            ↓
               Pydantic    Business Logic
               Validation
```

### Model Base Class

All models inherit from `Model` (in `app/models/model.py`), which provides:
- Automatic timestamps (`created_at`, `updated_at`)
- Soft delete support (`deleted_at` is an **Integer** timestamp, default `0`, not `NULL`)
- Laravel-like query methods: `find()`, `all()`, `where()`, `with_trashed()`, `only_trashed()`
- Laravel-like actions: `save()`, `delete()`, `force_delete()`, `restore()`

```python
# Usage examples
user = User.find(db, 1)           # Find by ID (excludes soft-deleted)
users = User.all(db)              # Get all non-deleted
User.where(db, email="x@y.com")   # Query with conditions
user.delete(db)                   # Soft delete
user.restore(db)                  # Restore soft-deleted
```

**Model field conventions:** All fields must specify `nullable` and a `default` value. Required fields use `nullable=False` with type-appropriate defaults (`''` for String/Text, `0` for Integer). Foreign keys use `nullable=False, default=0`. See `app/models/` for examples.

**Column ordering:** Concrete models explicitly redeclare `id`, `created_at`, `updated_at`, `deleted_at` (overriding the base class `@declared_attr`) to ensure columns appear in a defined order in SQLite. Follow this pattern for new models.

**Serialization:** Models can override `to_dict()` for custom output — e.g., `User.to_dict()` hides `hashed_password` and includes `roles`/`permissions`; models with `DateTime` fields format them via `.isoformat()`.

### Domain Model Relationships

```
User
├── projects (Project.user_id → users.id)
│   └── tasks (Task.project_id → projects.id)
│       └── messages (Message.task_id → tasks.id)
├── tasks (Task.user_id → users.id)
├── templates (Template.user_id → users.id)
└── roles (M2M via UserRole)
    └── permissions (M2M via RolePermission)
```

All ownership-aware routes enforce that users can only access their own resources (`user_id` is taken from `current_user.id` and filtered in Service queries).

### RBAC Models

Role-Based Access Control uses three join tables:
- `user_roles` — links User ↔ Role (many-to-many)
- `role_permissions` — links Role ↔ Permission (many-to-many)
- `User.to_dict()` automatically includes the user's `roles` and deduplicated `permissions`

Seed data: `admin` role gets all permissions; `user` role gets create+read on projects/tasks/messages.

### AI Chat System

The `/api/chat/` endpoint provides an LLM-powered bioinformatics assistant:
- Backed by **DashScope** (Alibaba Cloud) via OpenAI-compatible API (`config/llm.py`)
- Each chat auto-creates a `Task` if `task_id` isn't provided, then appends `Message` records
- `Message.role` is `"user"` or `"assistant"`; `Message.type` is one of `"text"`, `"path"`, `"code"`, `"file_request"`
- `AIService` sends conversation history to the LLM with a system prompt requiring structured JSON responses
- Falls back to placeholder responses when `DASHSCOPE_API_KEY` is missing or LLM call fails
- Config: `DASHSCOPE_API_KEY`, `DASHSCOPE_API_BASE`, `DASHSCOPE_MODEL_NAME` in `.env`

### Authentication

JWT-based auth using `python-jose` and `passlib`:
- Middleware: `app/http/middleware/auth_middleware.py` - exported as `Auth` dependency
- Service: `app/services/auth_service.py`
- Protected routes use: `current_user: User = Auth`

```python
from app.http.middleware import Auth

@router.get("/protected")
def protected_route(current_user: User = Auth):
    return current_user.to_dict()
```

Login returns `{"token": "...", "user": {...}}` (field name is `token`, not `access_token`). Token expiry is 7 days (`config/auth.py`).

### Adding New Features

To add a new resource (e.g., "Project"):

1. **Model** - Create `app/models/project.py`:
   ```python
   from sqlalchemy import String, Integer
   from app.models.model import Model

   class Project(Model):
       __tablename__ = "projects"
       name = Column(String, nullable=False)
   ```

2. **Service** - Create `app/services/project_service.py`:
   ```python
   class ProjectService:
       @staticmethod
       def create(name: str, db: Session):
           project = Project(name=name)
           return project.save(db)
   ```

3. **Controller** - Create `app/http/controllers/project_controller.py`:
   ```python
   class ProjectController:
       @staticmethod
       def create(name: str, db: Session):
           return ProjectService.create(name, db)
   ```

4. **Request** - Create `app/http/requests/project_request.py`:
   ```python
   class CreateProjectRequest(BaseModel):
       name: str = Field(min_length=1)
   ```

5. **Route** - Create `routes/projects.py`:
   ```python
   router = APIRouter(prefix="/projects", tags=["projects"])

   @router.post("/")
   def create(request: CreateProjectRequest, db: Session = Depends(get_db)):
       return ProjectController.create(request.name, db)
   ```

6. **Register** - Add to `routes/api.py`:
   ```python
   from routes.project import router as project_router
   router.include_router(project_router)
   ```

7. **Export** - Add to appropriate `__init__.py` files

8. **Migrate** - Run `python migrate_seed.py`

## Configuration

- Environment: `.env` (copy from `.env.example`)
- App config: `config/app.py`
- Database config: `config/database.py`
- Auth config: `config/auth.py` (JWT settings)
- LLM config: `config/llm.py` (DashScope API settings)

## Database

- SQLAlchemy ORM with SQLite (default)
- Connection: `database/connection.py`
- Sessions: Use `Depends(get_db)` dependency or `SessionLocal()`
- All tables auto-created via `migrate_seed.py`

## Utilities

- `pkg/helpers/time_helper.py` — `get_utc_now()` (DateTime factory), `get_timestamp()` (integer timestamp for `deleted_at`)

## Testing Accounts

After running `migrate_seed.py`:
- `admin@bioflow.com` / `admin123`
- `user@bioflow.com` / `user123`
