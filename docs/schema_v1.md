Project: Multi-Tenant Project Management SaaS

Multi-Tenant
Shared DB
Shared Schema

IDs:
UUID

User:
One Tenant per User
Soft Delete

Roles:
Global Roles
Owner
Admin
Member

Projects:
Belong to Tenant
Manager Optional

Tasks:
Belong to Project
Assigned to User
Status-based

Comments:
Belong to Task

Audit Logs:
Track Who
Did What
When

Entities:

Tenant
Role
User
Project
ProjectManager
Task
Comment
AuditLog

Tenant:
tenant_id (UUID, PK)
name (varchar, unique)
discription (varchar, notunique, can be null)
created_at (timestamp)
updated_at (timestamp)

Role:
Role_id(UUID, pk)
name (varchar, unique)
role_discription (varchar)
created_at (timestamp)

User
user_id (UUID, PK)
tenant_id (UUID, FK)
role_id (UUID, FK)
email (VARCHAR, UNIQUE)
hashed_password (VARCHAR)
full_name (VARCHAR)
is_active (BOOLEAN)
delteted_at (TIMESTAMP, nullable)
created_at
updated_at

Project
project_id (UUID PK)
tenant_id (UUID FK)
manager_id (UUID FK -> User)
name (VARCHAR)
description (TEXT)
status (ENUM/String)
created_at
updated_at

ProjectMember
project_id (UUID FK -> Project)
user_id (UUID FK -> User)
joined_at (TIMESTAMP)
PRIMARY KEY(project_id, user_id)

Task
task_id (UUID PK)
project_id (UUID FK)
assignee_id (UUID FK -> User)
title (VARCHAR)
description (TEXT)
status (ENUM/String)
priority (ENUM/String)
created_by (UUID FK -> User)
created_at
updated_at

Comment
comment_id (UUID PK)
task_id (UUID FK)
author_id (UUID FK -> User)
content (TEXT)
created_at
updated_at

AuditLog
audit_id (UUID PK)
user_id (UUID FK)
action (VARCHAR)
entity_type (VARCHAR)
entity_id (UUID)
description (TEXT)
created_at

config.py
↓
provides settings

session.py
↓
uses settings
↓
creates engine & sessions

base.py
↓
provides model foundation

models/
↓
inherit from Base

main.py
↓
starts FastAPI

Base
↑
User

Base
↑
Project

Base
↑
Task
