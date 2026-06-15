from typing import Optional

from pydantic import BaseModel, Field


class DataTypeInput(BaseModel):
    type_id: str = Field(min_length=1)
    label: str = ""
    description: str = ""
    extensions: list[str] = []
    required: bool = True
    multiple: bool = False
    is_uploadable: bool = False


class CreateDomainRequest(BaseModel):
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    description: str = ""
    keywords: str = ""
    script_root: str = "uploaded"
    categories: list[str] = []
    data_types: list[DataTypeInput] = []


class UpdateDomainRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    is_active: Optional[int] = None
