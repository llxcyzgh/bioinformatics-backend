from pydantic import BaseModel, Field


class CreateTaskRequest(BaseModel):
    """Create task request validation"""
    project_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=255)


class UpdateTaskRequest(BaseModel):
    """Update task request validation"""
    name: str | None = Field(None, min_length=1, max_length=255)


class RenameTaskRequest(BaseModel):
    """Rename task request validation"""
    name: str = Field(min_length=1, max_length=255)
