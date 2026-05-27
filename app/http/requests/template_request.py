from pydantic import BaseModel, Field


class CreateTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_public: bool = False
    scripts: str = Field(default='')


class UpdateTemplateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_public: bool | None = None
    scripts: str | None = None
