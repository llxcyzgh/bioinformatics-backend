from pydantic import BaseModel, EmailStr, Field


class CreateUserRequest(BaseModel):
    """Create user request validation"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    full_name: str | None = None


class UpdateUserRequest(BaseModel):
    """Update user request validation"""
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    full_name: str | None = None
