from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name:Optional[str]= Field(default=None, max_length=100)
    last_name: Optional[str]= Field(default=None, max_length=100)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    native_language: str
    target_language: str
    is_active: bool
    is_verified: bool
