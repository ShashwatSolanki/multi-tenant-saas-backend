import os
from pathlib import Path

DB_PATH = Path("test_aegis.db")
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ["DATABASE_URL"] = "sqlite:///./test_aegis.db"
os.environ["JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(client: TestClient, email: str, password: str):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_registration_login_and_health(client):
    response = client.post("/api/v1/auth/register", json={
        "tenant_name": "Acme Test",
        "full_name": "Owner User",
        "email": "owner@acme.test",
        "password": "password123",
    })
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert client.get("/health").json()["status"] == "ok"


def test_project_and_task_flow(client):
    headers = auth_headers(client, "owner@acme.test", "password123")
    project = client.post("/api/v1/projects", headers=headers, json={"name": "Aegis MVP"})
    assert project.status_code == 201
    project_id = project.json()["project_id"]

    task = client.post(f"/api/v1/projects/{project_id}/tasks", headers=headers, json={"title": "Ship API"})
    assert task.status_code == 201
    task_id = task.json()["task_id"]

    updated = client.patch(f"/api/v1/tasks/{task_id}", headers=headers, json={"status": "in_progress"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"

    comment = client.post(f"/api/v1/tasks/{task_id}/comments", headers=headers, json={"content": "Started"})
    assert comment.status_code == 201


def test_cross_tenant_project_isolation(client):
    response = client.post("/api/v1/auth/register", json={
        "tenant_name": "Other Tenant",
        "full_name": "Other Owner",
        "email": "owner@other.test",
        "password": "password123",
    })
    assert response.status_code == 201
    headers = auth_headers(client, "owner@other.test", "password123")
    projects = client.get("/api/v1/projects", headers=headers)
    assert projects.status_code == 200
    assert projects.json() == []
