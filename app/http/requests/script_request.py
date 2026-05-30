from typing import Optional

from pydantic import BaseModel, Field


class CreateScriptFolderRequest(BaseModel):
    name: str = Field(min_length=1)
    parent_id: int = Field(default=0)
    sort_order: int = Field(default=0)


class UpdateScriptFolderRequest(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None


class CreateScriptRequest(BaseModel):
    name: str = Field(min_length=1)
    folder_id: int = Field(default=0)
    tool_id: str = Field(default="")
    category: str = Field(default="")
    version: str = Field(default="1.0.0")
    runtime: int = Field(default=0)
    cost: float = Field(default=0.0)
    weight: int = Field(default=0)
    inputs: str = Field(default="[]")
    outputs: str = Field(default="[]")
    valid_from: str = Field(default="")
    valid_until: str = Field(default="")


class UpdateScriptRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    folder_id: int | None = None
    tool_id: str | None = None
    category: str | None = None
    version: str | None = None
    runtime: int | None = None
    cost: float | None = None
    weight: int | None = None
    inputs: str | None = None
    outputs: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
