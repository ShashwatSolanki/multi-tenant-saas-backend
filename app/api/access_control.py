from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import AuditLog, Project, ProjectMember, Task, TaskMember, User
from app.schemas import ProjectMemberResponse, ProjectResponse, TaskResponse, TaskUpdate, UserResponse

router = APIRouter()


def is_member(db: Session, project_id: UUID, user_id: UUID) -> bool:
    return db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)) is not None


def serialize_task(task: Task) -> dict:
    return {
        "task_id": task.task_id,
        "project_id": task.project_id,
        "assignee_id": task.assignee_id,
        "collaborator_ids": [member.user_id for member in task.collaborators],
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "created_by": task.created_by,
        "created_at": task.created_at,
    }


def project_for_user(db: Session, project_id: UUID, user: User) -> Project | None:
    project = db.scalar(select(Project).where(Project.project_id == project_id, Project.tenant_id == user.tenant_id))
    if not project:
        return None
    if user.role.name == "Member" and not is_member(db, project_id, user.user_id):
        raise HTTPException(403, "Members can only access projects assigned to them")
    return project


@router.get("/users", response_model=list[UserResponse])
def scoped_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role.name != "Member":
        users = db.scalars(select(User).where(User.tenant_id == user.tenant_id, User.deleted_at.is_(None)).order_by(User.created_at)).all()
    else:
        project_ids = select(ProjectMember.project_id).where(ProjectMember.user_id == user.user_id)
        users = db.scalars(
            select(User)
            .join(ProjectMember, ProjectMember.user_id == User.user_id)
            .where(User.tenant_id == user.tenant_id, User.deleted_at.is_(None), ProjectMember.project_id.in_(project_ids))
            .distinct()
            .order_by(User.created_at)
        ).all()
    return [{"user_id": u.user_id, "tenant_id": u.tenant_id, "email": u.email, "full_name": u.full_name, "role": u.role.name, "is_active": u.is_active} for u in users]


@router.get("/projects", response_model=list[ProjectResponse])
def scoped_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(Project).where(Project.tenant_id == user.tenant_id)
    if user.role.name == "Member":
        query = query.join(ProjectMember, ProjectMember.project_id == Project.project_id).where(ProjectMember.user_id == user.user_id)
    return list(db.scalars(query.order_by(Project.created_at.desc())))


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def scoped_project(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = project_for_user(db, project_id, user)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberResponse])
def scoped_project_members(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = project_for_user(db, project_id, user)
    if not project:
        raise HTTPException(404, "Project not found")
    rows = db.execute(select(ProjectMember, User).join(User, User.user_id == ProjectMember.user_id).where(ProjectMember.project_id == project_id, User.tenant_id == user.tenant_id)).all()
    return [ProjectMemberResponse(user_id=u.user_id, full_name=u.full_name, email=u.email, role=u.role.name, joined_at=link.joined_at) for link, u in rows]


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
def scoped_tasks(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = project_for_user(db, project_id, user)
    if not project:
        raise HTTPException(404, "Project not found")
    tasks = db.scalars(select(Task).join(Project).where(Task.project_id == project_id, Project.tenant_id == user.tenant_id).order_by(Task.created_at.desc())).all()
    if user.role.name == "Member":
        tasks = [task for task in tasks if task.assignee_id == user.user_id or task.created_by == user.user_id or any(member.user_id == user.user_id for member in task.collaborators)]
    return [serialize_task(task) for task in tasks]


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def scoped_task_update(task_id: UUID, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.scalar(select(Task).join(Project).where(Task.task_id == task_id, Project.tenant_id == user.tenant_id))
    if not task:
        raise HTTPException(404, "Task not found")
    is_participant = task.assignee_id == user.user_id or task.created_by == user.user_id or db.scalar(select(TaskMember).where(TaskMember.task_id == task_id, TaskMember.user_id == user.user_id)) is not None
    payload = data.model_dump(exclude_unset=True)
    if user.role.name == "Member":
        if not is_participant:
            raise HTTPException(403, "Members may only update tasks assigned to, created by, or collaborated on by them")
        forbidden = set(payload) - {"status", "description"}
        if forbidden:
            raise HTTPException(403, "Members may only change task status and description")
    if "assignee_id" in payload:
        assignee = db.scalar(select(User).where(User.user_id == payload["assignee_id"], User.tenant_id == user.tenant_id, User.deleted_at.is_(None), User.is_active.is_(True)))
        if not assignee or not is_member(db, task.project_id, assignee.user_id):
            raise HTTPException(400, "Assignee must be an active member of the project")
    for field, value in payload.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return serialize_task(task)


@router.get("/audit-logs")
def scoped_audit_logs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role.name == "Member":
        raise HTTPException(403, "Audit logs are restricted to Owners and Admins")
    stmt = select(AuditLog).join(User, AuditLog.user_id == User.user_id).where(User.tenant_id == user.tenant_id).order_by(AuditLog.created_at.desc())
    return db.scalars(stmt).all()
