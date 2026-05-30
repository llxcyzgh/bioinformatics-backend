from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    task_id: Optional[int] = None
    project_id: int = Field(gt=0)
    content: str = Field(min_length=1)
    type: str = Field(default="text")


class ConfirmPathRequest(BaseModel):
    task_uuid: str = Field(min_length=1)
    project_id: int = Field(default=0)
    candidate_id: str = Field(min_length=1)
    candidate_data: str = Field(min_length=1)
