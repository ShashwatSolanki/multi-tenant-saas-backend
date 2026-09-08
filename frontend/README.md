# Aegis Frontend

React/Vite dashboard for Project Aegis.

## Run

From `frontend/`:

```bash
npm install
npm run dev
```

The UI expects the FastAPI backend at `http://localhost:8000/api/v1`. Set `VITE_API_URL` to override it.

## Demo flow

1. Start the backend.
2. Open the Vite URL shown in the terminal (normally `http://localhost:5173`).
3. Register a tenant to create the initial Owner.
4. Use the dashboard to inspect projects, tasks, team members and audit logs.

The frontend is intentionally a thin client: authentication and authorization remain enforced by the Aegis API.
