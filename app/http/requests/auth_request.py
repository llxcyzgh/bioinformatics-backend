from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request validation
    Similar to Laravel's FormRequest
    """
    email: EmailStr
    password: str = Field(min_length=6)


class RegisterRequest(BaseModel):
    """Register request validation"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    full_name: str | None = None
