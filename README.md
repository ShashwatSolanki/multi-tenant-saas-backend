# Project Aegis — Multi-Tenant Project Management SaaS

Project Aegis is a multi-tenant project-management SaaS application built around the original Aegis architecture: **shared PostgreSQL database, shared schema, UUID identifiers, JWT authentication, RBAC, tenant-context middleware, tenant-scoped queries, and audit logging**.

The repository contains both the **FastAPI backend** and a lightweight **React/Vite GUI** for demonstrating the system end-to-end.

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
- Backend-enforced role permissions
- Tenant context middleware
- Tenant-isolated project listing and lookup
- Project creation with description and same-tenant manager validation
- Workspace user creation for Owners/Admins
- Owner can create Admin or Member accounts; Admin can create Member accounts
- Project tasks with same-tenant assignee validation
- Task creation restricted to Owner/Admin
- Member task updates restricted to tasks assigned to or created by that Member
- Task status, description and priority support (`high`, `medium`, `low`)
- Task comments
- Audit logs for project, task, comment and user mutations
- Tenant verification endpoint that validates the authenticated tenant against the database tenant record
- Soft-delete support on users
- SQLAlchemy UUID-based domain model
- PostgreSQL Docker development stack
- Health and database connectivity endpoints
- Automated API tests for authentication, CRUD flow, role enforcement, task permissions and tenant isolation
- Interactive OpenAPI documentation

### GUI

The frontend is located in `frontend/` and provides an end-to-end demonstration dashboard:

- Login / workspace registration
- Tenant workspace dashboard
- Project creation with description and optional manager
- Task creation with description, priority and assignee
- Priority-ordered task board
- Team management with visible Owner/Admin/Member roles
- Role-aware Add User controls
- Tenant Verification page showing tenant ID and verification checks
- Audit log view for Owners/Admins
- Sign out
- Responsive layout

The GUI talks to the same FastAPI API, so tenant isolation and RBAC remain **backend-enforced** rather than being trusted to the browser.

## RBAC Permissions

| Capability | Owner | Admin | Member |
|---|:---:|:---:|:---:|
| View own tenant data | ✓ | ✓ | ✓ |
| Create Admin users | ✓ | — | — |
| Create Member users | ✓ | ✓ | — |
| Create projects | ✓ | ✓ | — |
| Create tasks | ✓ | ✓ | — |
| Update tasks | ✓ | ✓ | Own/assigned |
| View audit logs | ✓ | ✓ | — |
| Verify current tenant context | ✓ | ✓ | ✓ |

The API applies these permissions independently of the GUI. A Member cannot bypass the interface restriction by calling the task-creation endpoint directly.

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
├── tests/                   # API, RBAC and tenant-isolation tests
├── .github/workflows/       # GitHub Actions CI
├── Dockerfile               # Backend container
├── docker-compose.yml       # PostgreSQL + API + frontend
├── .env.example             # Backend environment template
└── requirements.txt         # Python dependencies
```

## Run the Complete Application with Docker

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

Open the frontend first at `http://localhost:5173`, create a workspace, and sign in as the Owner.

### Suggested demo flow

1. Register a new workspace.
2. Open **Team & roles** and add a Member and an Admin.
3. Create a project with a description and optional manager.
4. Open the project and create High/Medium/Low priority tasks with assignees.
5. Open **Tasks** and use **Priority order** to see High → Medium → Low ordering.
6. Open **Tenant verification** and run **Verify tenant context**.
7. Open **Audit logs** to show the recorded actions.
8. Sign in as the Member to demonstrate that task creation is rejected while permitted task updates remain available.

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
| GET | `/api/v1/me` | Current authenticated user and role |
| GET | `/api/v1/tenant` | Verify current tenant context and return tenant details |
| POST | `/api/v1/users` | Owner/Admin creates tenant user |
| GET | `/api/v1/users` | List tenant users and roles |
| POST | `/api/v1/projects` | Create project (Owner/Admin) |
| GET | `/api/v1/projects` | List current tenant projects |
| GET | `/api/v1/projects/{project_id}` | Get tenant-scoped project |
| POST | `/api/v1/projects/{project_id}/tasks` | Create task (Owner/Admin) |
| GET | `/api/v1/projects/{project_id}/tasks` | List project tasks |
| PATCH | `/api/v1/tasks/{task_id}` | Update task according to RBAC |
| POST | `/api/v1/tasks/{task_id}/comments` | Add comment |
| GET | `/api/v1/tasks/{task_id}/comments` | List comments |
| GET | `/api/v1/audit-logs` | Owner/Admin audit view |

## Security and Tenant Isolation

A JWT carries `user_id`, `tenant_id`, and `role`. Protected requests validate the token and load the user using both the user ID and tenant ID. Tenant-owned reads and writes additionally constrain the tenant ID.

This means a user from Tenant B cannot access Tenant A's projects, tasks, comments, managers, or assignees simply by knowing their IDs. The test suite creates separate tenants and verifies that tenant-scoped project data is isolated.

The `/api/v1/tenant` endpoint provides an explicit runtime verification of the authenticated tenant context by checking that the JWT's tenant identity resolves to the corresponding database tenant and that the current user belongs to it.

## Tests

Run the backend test suite with:

```bash
python -m pytest -q
```

The tests cover:

1. Tenant registration and Owner creation
2. JWT login
3. Health endpoint
4. Tenant context verification
5. Owner user creation and role assignment
6. Member project/task permission enforcement
7. Project creation with description
8. Task creation with priority
9. Task update and comment flow
10. Cross-tenant project isolation

GitHub Actions runs the backend test suite and a production frontend build automatically on pushes and pull requests targeting `main`.

## Test Run / Screenshots

Runtime screenshots should be captured from the locally running application rather than fabricated in documentation.

Recommended screenshots for a project/demo report are:

1. Login / workspace registration screen
2. Dashboard after login
3. Project creation form showing description and manager
4. Team page showing Owner/Admin/Member roles and Add User
5. Task creation form showing priority and assignee
6. Task board showing priority ordering
7. Tenant Verification page showing PASS checks
8. Audit log page
9. Swagger `/docs` page
10. Terminal showing a successful `python -m pytest -q` run
11. GitHub Actions page showing the green Aegis CI workflow

After running the stack locally, place real screenshots under `docs/images/screenshots/` and reference them from this section if desired. This keeps repository evidence authentic and tied to an actual run.

## CI

The GitHub Actions workflow has two checks:

- **Backend:** installs the Python dependencies and runs `python -m pytest -q` with `PYTHONPATH=.` so the `app` package is resolved reliably in the runner.
- **Frontend:** installs the React/Vite dependencies with Node.js 22 and runs `npm run build` to catch GUI compilation errors.

## Original Design Documents

The original Aegis design material remains available in `docs/`:

- `docs/schema_v1.md` — schema and entity design
- `docs/images/hld.png` — high-level architecture
- `docs/images/workflow.png` — workflow/request flow
- `docs/images/sequence.png` — sequence diagram

These documents describe the foundation on which the implementation was completed.

## Project Status

**Aegis MVP implementation complete.** The repository contains the backend, GUI, database setup, authentication, RBAC, tenant isolation, tenant-context verification, audit logging, tests, Docker configuration, CI workflow, and original design documentation.
