from fastapi import HTTPException
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models.models import Project, ProjectMember, Task, TaskMember, User


def _active_user(session: Session, user_id, tenant_id) -> bool:
    if user_id is None:
        return True
    user = session.get(User, user_id)
    return bool(user and user.tenant_id == tenant_id and user.deleted_at is None and user.is_active)


@event.listens_for(Session, "before_flush")
def enforce_active_assignments(session: Session, flush_context, instances) -> None:
    for obj in list(session.new) + list(session.dirty):
        state = inspect(obj)

        if isinstance(obj, Project) and (obj in session.new or state.attrs.manager_id.history.has_changes()):
            if obj.manager_id is not None and not _active_user(session, obj.manager_id, obj.tenant_id):
                raise HTTPException(400, "Project manager must be an active user in the tenant")

        if isinstance(obj, ProjectMember) and obj in session.new:
            project = session.get(Project, obj.project_id)
            user = session.get(User, obj.user_id)
            if not project or not user or user.tenant_id != project.tenant_id or user.deleted_at is not None or not user.is_active:
                raise HTTPException(400, "Project member must be an active user in the same tenant")

        if isinstance(obj, Task) and (obj in session.new or state.attrs.assignee_id.history.has_changes()):
            if obj.assignee_id is not None:
                project = session.get(Project, obj.project_id)
                tenant_id = project.tenant_id if project else None
                if not _active_user(session, obj.assignee_id, tenant_id):
                    raise HTTPException(400, "Task assignee must be an active user in the tenant")

        if isinstance(obj, TaskMember) and obj in session.new:
            task = session.get(Task, obj.task_id)
            project = session.get(Project, task.project_id) if task else None
            if not project or not _active_user(session, obj.user_id, project.tenant_id):
                raise HTTPException(400, "Task collaborator must be an active user in the tenant")
