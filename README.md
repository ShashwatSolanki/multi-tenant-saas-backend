# Project Aegis — Multi-Tenant Project Management SaaS

Project Aegis is a multi-tenant project-management SaaS application built around the original Aegis architecture: **shared PostgreSQL database, shared schema, UUID identifiers, JWT authentication, RBAC, tenant-context middleware, tenant-scoped queries, and audit logging**.

The repository now contains both the **FastAPI backend** and a lightweight **React/Vite GUI** for demonstrating the system end-to-end.

## Architecture

![Aegis High-Level Design](docs/images/hld.png)

**Request flow:**

Client → JWT Authentication → Tenant Context Middleware → RBAC → Business/API Layer → SQLAlchemy → PostgreSQL

![Aegis Workflow](docs/images/workflow.png)

The database uses a shared-schema multi-tenant model. Tenant-owned resources are scoped to the authenticated user's `tenant_id`, and protected queries validate tenant ownership before returning or modifying data.

## Sequence

![Aegis Sequence Diagram](docs/images/sequence.png)

The original architecture diagrams and schema document are retained under `docs/`.

## Features

### Backend

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
- Soft-delete support on users
- SQLAlchemy UUID-based domain model
- PostgreSQL Docker development stack
- Health and database connectivity endpoints
- Automated API tests for authentication, CRUD flow, and tenant isolation
- Interactive OpenAPI documentation

### GUI

The frontend is located in `frontend/` and provides a simple demonstration dashboard:

- Login / registration
- Tenant workspace dashboard
- Projects view
- Task board
- Team and role view
- Audit log view
- Sign out
- Responsive layout

The GUI talks to the same FastAPI API, so tenant isolation and RBAC remain **backend-enforced** rather than being trusted to the browser.

## Database Model

The schema follows the original Aegis design:

`Tenant → User / Role → Project → ProjectMember → Task → Comment`

with `AuditLog` recording security-relevant actions.

The complete original schema is documented in [`docs/schema_v1.md`](docs/schema_v1.md).

## Project Structure

```text
.
├── app/
│   ├── api/                 # API routes and dependencies
│   ├── core/                # Configuration and security
│   ├── db/                  # SQLAlchemy engine, session and initialization
│   ├── middleware/          # Tenant context middleware
│   ├── models/              # SQLAlchemy domain models
│   ├── main.py              # FastAPI application entry point
│   └── schemas.py            # Pydantic request/response schemas
├── docs/
│   ├── images/              # Original HLD, workflow and sequence diagrams
│   └── schema_v1.md         # Original schema/design document
├── frontend/                # React/Vite GUI
├── tests/                   # API and tenant-isolation tests
├── .github/workflows/       # GitHub Actions CI
├── Dockerfile               # Backend container
├── docker-compose.yml       # PostgreSQL + API + frontend
├── .env.example             # Backend environment template
└── requirements.txt         # Python dependencies
```

## Run the Complete Application with Docker

Clone the repository and start all services:

```bash
git clone https://github.com/ShashwatSolanki/multi-tenant-saas-backend.git
cd multi-tenant-saas-backend
docker compose up --build
```

Services:

| Service | URL | Purpose |
|---|---|---|
| Frontend | `http://localhost:5173` | Aegis GUI |
| API | `http://localhost:8000` | FastAPI backend |
| Swagger | `http://localhost:8000/docs` | Interactive API documentation |
| Database | `localhost:5432` | PostgreSQL |

Open the frontend first at `http://localhost:5173`, create a workspace, and sign in.

## Run Backend Without Docker

Create a virtual environment, install the dependencies, and configure `.env` from `.env.example`.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

For the intended architecture, configure PostgreSQL through `DATABASE_URL`. The test suite overrides the database with a temporary SQLite database.

## Run Frontend Without Docker

```bash
cd frontend
npm install
npm run dev
```

The Vite development server runs at `http://localhost:5173` and connects to `http://localhost:8000/api/v1` by default.

## Core API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Create tenant + Owner |
| POST | `/api/v1/auth/login` | Obtain JWT |
| GET | `/api/v1/me` | Current authenticated user |
| POST | `/api/v1/users` | Create tenant user |
| GET | `/api/v1/users` | List tenant users |
| POST | `/api/v1/projects` | Create project (Owner/Admin) |
| GET | `/api/v1/projects` | List current tenant projects |
| GET | `/api/v1/projects/{project_id}` | Get tenant-scoped project |
| POST | `/api/v1/projects/{project_id}/tasks` | Create task |
| GET | `/api/v1/projects/{project_id}/tasks` | List project tasks |
| PATCH | `/api/v1/tasks/{task_id}` | Update task |
| POST | `/api/v1/tasks/{task_id}/comments` | Add comment |
| GET | `/api/v1/tasks/{task_id}/comments` | List comments |
| GET | `/api/v1/audit-logs` | Owner/Admin audit view |

## Security and Tenant Isolation

A JWT carries `user_id`, `tenant_id`, and `role`. Protected requests validate the token and load the user using both the user ID and tenant ID. Tenant-owned reads and writes additionally constrain the tenant ID.

This means a user from Tenant B cannot access Tenant A's projects, tasks, comments, managers, or assignees simply by knowing their IDs.

## Tests

Run the complete backend test suite with:

```bash
python -m pytest -q
```

The tests cover:

1. Tenant registration and Owner creation
2. JWT login
3. Health endpoint
4. Project creation
5. Task creation and update
6. Comment creation
7. Cross-tenant project isolation

GitHub Actions runs the same test suite automatically on pushes and pull requests targeting `main`.

## Test Run / Screenshots

The repository includes the architecture diagrams above as the stable project documentation. **Runtime screenshots should be captured from the locally running application rather than fabricated in documentation.**

Recommended screenshots for a project/demo report are:

1. Login / workspace registration screen
2. Dashboard after login
3. Projects page with a created project
4. Task board showing Todo / In Progress / Done
5. Team page showing Owner/Admin/Member roles
6. Audit log page
7. Swagger `/docs` page
8. Terminal showing a successful `pytest -q` run

After running the stack locally, these can be added under `docs/images/screenshots/` and referenced here without changing the application architecture.

## CI

The project uses GitHub Actions for automated backend tests. The workflow installs the pinned Python dependencies and executes `python -m pytest -q` with the repository root on `PYTHONPATH` so the `app` package is resolved reliably in the runner.

## Original Design Documents

The original Aegis design material remains available in `docs/`:

- `docs/schema_v1.md` — schema and entity design
- `docs/images/hld.png` — high-level architecture
- `docs/images/workflow.png` — request/workflow diagram
- `docs/images/sequence.png` — sequence diagram

These documents describe the foundation on which the implementation was completed.

## Project Status

**Aegis MVP implementation complete.** The repository contains the backend, GUI, database setup, authentication, RBAC, tenant isolation, audit logging, tests, Docker configuration, CI workflow, and original design documentation.
