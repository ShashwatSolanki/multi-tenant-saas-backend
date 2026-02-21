from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    organization_id: UUID


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    organization_id: UUID
    is_active: bool

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    organization_id: str