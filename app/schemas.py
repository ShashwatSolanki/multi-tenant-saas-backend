from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import ProjectStatus, TaskPriority, TaskStatus


class RegisterRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=120)
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=72)
    role: Literal["Admin", "Member"] = "Member"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: str


class TenantResponse(BaseModel):
    tenant_id: UUID
    name: str
    description: str | None
    member_count: int
    verification: dict[str, bool]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    manager_id: UUID | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    manager_id: UUID | None = None
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: UUID
    tenant_id: UUID
    manager_id: UUID | None
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime


class ProjectMemberCreate(BaseModel):
    user_id: UUID


class ProjectMemberResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    role: str
    joined_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    assignee_id: UUID | None = None
    collaborator_ids: list[UUID] = Field(default_factory=list, max_length=50)
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    assignee_id: UUID | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None


class TaskResponse(BaseModel):
    task_id: UUID
    project_id: UUID
    assignee_id: UUID | None
    collaborator_ids: list[UUID]
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_by: UUID
    created_at: datetime


class TaskCollaboratorsUpdate(BaseModel):
    user_ids: list[UUID] = Field(default_factory=list, max_length=50)


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    comment_id: UUID
    task_id: UUID
    author_id: UUID
    content: str
    created_at: datetime
