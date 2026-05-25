# Model Field Conventions

## Why
Ensures consistent database schema and prevents NULL-related issues in queries and API responses.

## How to Apply
All model fields MUST follow these conventions:

### String Fields
```python
name = Column(String, nullable=False, default='')
description = Column(String, nullable=True, default='')
```

### Integer Fields
```python
user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=0)
count = Column(Integer, nullable=False, default=0)
```

### Text Fields
```python
content = Column(Text, nullable=False, default='')
data = Column(Text, nullable=True, default='')
```

### DateTime Fields
```python
created_at = Column(DateTime, default=get_utc_now, nullable=False)
updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
deleted_at = Column(Integer, default=0, nullable=False)  # Soft delete using timestamp
```

## Rules
1. **Always specify `nullable=False`** for required fields
2. **Always provide `default`** value matching the field type:
   - String/Text → `''` (empty string)
   - Integer → `0`
   - DateTime → `get_utc_now()`
3. **Soft delete uses Integer** with `default=0` (not NULL)
4. **Foreign keys** should have `nullable=False, default=0` unless explicitly optional

## Example: Complete Model
```python
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now

class Task(Model):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    uuid = Column(String, unique=True, index=True, nullable=False, default='')
    name = Column(String, nullable=False, default='')
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=0)
```
