from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import ProjectStatus, TaskPriority, TaskStatus


class RegisterRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=120)
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    tenant_id: UUID
    email: EmailStr
    full_name: str
    role: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    manager_id: UUID | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: UUID
    tenant_id: UUID
    manager_id: UUID | None
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    assignee_id: UUID | None = None
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    assignee_id: UUID | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: UUID
    project_id: UUID
    assignee_id: UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_by: UUID
    created_at: datetime


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    comment_id: UUID
    task_id: UUID
    author_id: UUID
    content: str
    created_at: datetime
