# Project Aegis — Multi-Tenant SaaS Backend

Project Aegis is a working, resume-grade multi-tenant project-management backend built around the original architecture: **shared PostgreSQL database, shared schema, UUID identifiers, JWT authentication, RBAC, middleware tenant context, tenant-scoped queries, and audit logging**.

## Architecture

Client → FastAPI → JWT Authentication → Tenant Context Middleware → RBAC → Business/API Layer → SQLAlchemy → PostgreSQL

The database uses a shared-schema model. Every tenant-owned resource carries a tenant discriminator and protected queries explicitly constrain records to the authenticated user's `tenant_id`.

## Implemented Features

- Tenant registration with an initial Owner account
- JWT login and stateless authentication
- Owner / Admin / Member RBAC
- Tenant context middleware
- Tenant-isolated project listing and lookup
- Project creation with same-tenant manager validation
- Project tasks with same-tenant assignee validation
- Task status and priority updates
- Task comments
- Audit logs for project, task, and comment mutations
- Soft-delete fields on users
- SQLAlchemy UUID-based domain model
- PostgreSQL Docker development stack
- API health and database connectivity endpoints
- Automated API tests covering authentication, CRUD flow, and tenant isolation
- Interactive OpenAPI documentation at `/docs`

## Database Model

The schema follows the original design: Tenant, Role, User, Project, ProjectMember, Task, Comment, and AuditLog. Projects belong to a tenant, tasks belong to projects, comments belong to tasks, and audit logs record who performed an action and on which entity.

## Run locally with Docker

```bash
git clone https://github.com/ShashwatSolanki/multi-tenant-saas-backend.git
cd multi-tenant-saas-backend
docker compose up --build
```

Then open `http://localhost:8000/docs` and use the API interactively.

## Run locally without Docker

Create a virtual environment, install `requirements.txt`, and configure `.env` using `.env.example`.

For a quick local demo, the application defaults to SQLite when `DATABASE_URL` is not supplied. For the intended deployment architecture, use PostgreSQL.

```bash
uvicorn app.main:app --reload
```

## Core API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Create tenant + Owner |
| POST | `/api/v1/auth/login` | Obtain JWT |
| GET | `/api/v1/me` | Current authenticated user |
| POST | `/api/v1/projects` | Create project (Owner/Admin) |
| GET | `/api/v1/projects` | List current tenant projects |
| GET | `/api/v1/projects/{project_id}` | Get tenant-scoped project |
| POST | `/api/v1/projects/{project_id}/tasks` | Create task |
| GET | `/api/v1/projects/{project_id}/tasks` | List project tasks |
| PATCH | `/api/v1/tasks/{task_id}` | Update task |
| POST | `/api/v1/tasks/{task_id}/comments` | Add comment |
| GET | `/api/v1/tasks/{task_id}/comments` | List comments |
| GET | `/api/v1/audit-logs` | Owner/Admin audit view |

## Security / Tenant Isolation

A JWT carries `user_id`, `tenant_id`, and `role`. On protected requests, the API validates the token and then loads the user using **both user ID and tenant ID**. Tenant-owned database reads and writes additionally constrain the tenant ID. Cross-tenant project, task, comment, manager, and assignee access therefore returns `404` or `400` instead of exposing another tenant's data.

## Tests

```bash
pytest -q
```

The test suite verifies registration/login, the project → task → comment flow, and that a second tenant cannot see the first tenant's projects.

## Project Status

**Implementation complete for the defined Aegis MVP architecture and schema.** The repository is runnable and exposes an interactive FastAPI/OpenAPI surface for demonstration and evaluation.
