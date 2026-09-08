from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.models import AuditLog, Comment, Project, ProjectMember, Role, Task, Tenant, User
from app.schemas import (
    CommentCreate, CommentResponse, LoginRequest, ProjectCreate, ProjectResponse,
    ProjectUpdate, RegisterRequest, TaskCreate, TaskResponse, TaskUpdate,
    TenantResponse, TokenResponse, UserCreate, UserResponse,
)

router = APIRouter()


def audit(db: Session, user: User, action: str, entity_type: str, entity_id: UUID, description: str) -> None:
    db.add(AuditLog(user_id=user.user_id, action=action, entity_type=entity_type, entity_id=entity_id, description=description))


def same_tenant_user(db: Session, user_id: UUID, tenant_id: UUID) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id, User.tenant_id == tenant_id, User.deleted_at.is_(None)))


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email already registered")
    if db.scalar(select(Tenant).where(Tenant.name == data.tenant_name)):
        raise HTTPException(409, "Tenant name already exists")
    owner_role = db.scalar(select(Role).where(Role.name == "Owner"))
    tenant = Tenant(name=data.tenant_name)
    db.add(tenant)
    db.flush()
    user = User(tenant_id=tenant.tenant_id, role_id=owner_role.role_id, email=data.email.lower(), hashed_password=hash_password(data.password), full_name=data.full_name)
    db.add(user)
    db.flush()
    audit(db, user, "create", "tenant", tenant.tenant_id, "Tenant registered")
    db.commit()
    return TokenResponse(access_token=create_access_token(user.user_id, tenant.tenant_id, owner_role.name))


@router.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower(), User.deleted_at.is_(None)))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User is inactive")
    return TokenResponse(access_token=create_access_token(user.user_id, user.tenant_id, user.role.name))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return {"user_id": user.user_id, "tenant_id": user.tenant_id, "email": user.email, "full_name": user.full_name, "role": user.role.name}


@router.get("/tenant", response_model=TenantResponse)
def get_tenant(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tenant = db.scalar(select(Tenant).where(Tenant.tenant_id == user.tenant_id))
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    member_count = db.scalar(select(func.count(User.user_id)).where(User.tenant_id == tenant.tenant_id, User.deleted_at.is_(None))) or 0
    return TenantResponse(tenant_id=tenant.tenant_id, name=tenant.name, description=tenant.description, member_count=member_count, verification={"tenant_exists": True, "user_belongs_to_tenant": user.tenant_id == tenant.tenant_id, "database_tenant_match": True})


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("Owner", "Admin"))):
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email already registered")
    if data.role == "Admin" and user.role.name != "Owner":
        raise HTTPException(403, "Only Owners can create Admin users")
    role = db.scalar(select(Role).where(Role.name == data.role))
    if not role:
        raise HTTPException(400, "Invalid role")
    new_user = User(tenant_id=user.tenant_id, role_id=role.role_id, email=data.email.lower(), hashed_password=hash_password(data.password), full_name=data.full_name)
    db.add(new_user)
    db.flush()
    audit(db, user, "create", "user", new_user.user_id, f"Created {data.role} user {new_user.email}")
    db.commit()
    db.refresh(new_user)
    return {"user_id": new_user.user_id, "tenant_id": new_user.tenant_id, "email": new_user.email, "full_name": new_user.full_name, "role": role.name}


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    users = db.scalars(select(User).where(User.tenant_id == user.tenant_id, User.deleted_at.is_(None)).order_by(User.created_at)).all()
    return [{"user_id": u.user_id, "tenant_id": u.tenant_id, "email": u.email, "full_name": u.full_name, "role": u.role.name} for u in users]


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("Owner", "Admin"))):
    if data.manager_id and not same_tenant_user(db, data.manager_id, user.tenant_id):
        raise HTTPException(400, "Manager must belong to the same tenant")
    project = Project(tenant_id=user.tenant_id, manager_id=data.manager_id, name=data.name, description=data.description)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.project_id, user_id=user.user_id))
    audit(db, user, "create", "project", project.project_id, f"Created project {project.name}")
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Project).where(Project.tenant_id == user.tenant_id).order_by(Project.created_at.desc())))


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = db.scalar(select(Project).where(Project.project_id == project_id, Project.tenant_id == user.tenant_id))
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: UUID, data: ProjectUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("Owner", "Admin"))):
    project = db.scalar(select(Project).where(Project.project_id == project_id, Project.tenant_id == user.tenant_id))
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status == "archived" and any(value is not None for value in data.model_dump(exclude_unset=True).values()):
        raise HTTPException(409, "Archived projects cannot be edited")
    if data.manager_id is not None and not same_tenant_user(db, data.manager_id, user.tenant_id):
        raise HTTPException(400, "Manager must belong to the same tenant")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    audit(db, user, "update", "project", project.project_id, f"Updated project {project.name}")
    db.commit()
    db.refresh(project)
    return project


@router.post("/projects/{project_id}/archive", response_model=ProjectResponse)
def archive_project(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles("Owner", "Admin"))):
    project = db.scalar(select(Project).where(Project.project_id == project_id, Project.tenant_id == user.tenant_id))
    if not project:
        raise HTTPException(404, "Project not found")
    project.status = "archived"
    audit(db, user, "archive", "project", project.project_id, f"Archived project {project.name}")
    db.commit()
    db.refresh(project)
    return project


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201)
def create_task(project_id: UUID, data: TaskCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("Owner", "Admin"))):
    project = db.scalar(select(Project).where(Project.project_id == project_id, Project.tenant_id == user.tenant_id))
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status == "archived":
        raise HTTPException(409, "Archived projects cannot receive new tasks")
    if data.assignee_id and not same_tenant_user(db, data.assignee_id, user.tenant_id):
        raise HTTPException(400, "Assignee must belong to the same tenant")
    task = Task(project_id=project.project_id, assignee_id=data.assignee_id, title=data.title, description=data.description, priority=data.priority, created_by=user.user_id)
    db.add(task)
    db.flush()
    audit(db, user, "create", "task", task.task_id, f"Created task {task.title}")
    db.commit()
    db.refresh(task)
    return task


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
def list_tasks(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.scalar(select(Project.project_id).where(Project.project_id == project_id, Project.tenant_id == user.tenant_id)):
        raise HTTPException(404, "Project not found")
    return list(db.scalars(select(Task).join(Project).where(Task.project_id == project_id, Project.tenant_id == user.tenant_id).order_by(Task.created_at.desc())))


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.scalar(select(Task).join(Project).where(Task.task_id == task_id, Project.tenant_id == user.tenant_id))
    if not task:
        raise HTTPException(404, "Task not found")
    if user.role.name == "Member" and task.assignee_id != user.user_id and task.created_by != user.user_id:
        raise HTTPException(403, "Members may only update their own tasks")
    if data.assignee_id and not same_tenant_user(db, data.assignee_id, user.tenant_id):
        raise HTTPException(400, "Assignee must belong to the same tenant")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    audit(db, user, "update", "task", task.task_id, f"Updated task {task.title}")
    db.commit()
    db.refresh(task)
    return task


@router.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(task_id: UUID, data: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.scalar(select(Task).join(Project).where(Task.task_id == task_id, Project.tenant_id == user.tenant_id))
    if not task:
        raise HTTPException(404, "Task not found")
    comment = Comment(task_id=task.task_id, author_id=user.user_id, content=data.content)
    db.add(comment)
    db.flush()
    audit(db, user, "create", "comment", comment.comment_id, "Added task comment")
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/tasks/{task_id}/comments", response_model=list[CommentResponse])
def list_comments(task_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.scalar(select(Task.task_id).join(Project).where(Task.task_id == task_id, Project.tenant_id == user.tenant_id)):
        raise HTTPException(404, "Task not found")
    return list(db.scalars(select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)))


@router.get("/audit-logs")
def list_audit_logs(db: Session = Depends(get_db), user: User = Depends(require_roles("Owner", "Admin"))):
    stmt = select(AuditLog).join(User, AuditLog.user_id == User.user_id).where(User.tenant_id == user.tenant_id).order_by(AuditLog.created_at.desc())
    return db.scalars(stmt).all()
