from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    """Create project request validation"""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class UpdateProjectRequest(BaseModel):
    """Update project request validation"""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
