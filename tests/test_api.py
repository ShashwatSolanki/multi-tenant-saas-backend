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


def test_registration_login_health_and_tenant_verification(client):
    response = client.post("/api/v1/auth/register", json={"tenant_name": "Acme Test", "full_name": "Owner User", "email": "owner@acme.test", "password": "password123"})
    assert response.status_code == 201
    assert client.get("/health").json()["status"] == "ok"
    headers = auth_headers(client, "owner@acme.test", "password123")
    tenant = client.get("/api/v1/tenant", headers=headers)
    assert tenant.status_code == 200 and all(tenant.json()["verification"].values())


def test_owner_can_add_users_and_roles_are_enforced(client):
    headers = auth_headers(client, "owner@acme.test", "password123")
    response = client.post("/api/v1/users", headers=headers, json={"full_name": "Member User", "email": "member@acme.test", "password": "password123", "role": "Member"})
    assert response.status_code == 201 and response.json()["role"] == "Member"
    response = client.post("/api/v1/users", headers=headers, json={"full_name": "Admin User", "email": "admin@acme.test", "password": "password123", "role": "Admin"})
    assert response.status_code == 201 and response.json()["role"] == "Admin"
    member_headers = auth_headers(client, "member@acme.test", "password123")
    assert client.post("/api/v1/projects", headers=member_headers, json={"name": "Denied"}).status_code == 403


def test_project_lifecycle_and_task_flow(client):
    headers = auth_headers(client, "owner@acme.test", "password123")
    project = client.post("/api/v1/projects", headers=headers, json={"name": "Aegis MVP", "description": "Secure multi-tenant project"})
    assert project.status_code == 201
    project_id = project.json()["project_id"]
    updated_project = client.patch(f"/api/v1/projects/{project_id}", headers=headers, json={"name": "Aegis Production MVP", "description": "Production-ready secure workspace", "status": "completed"})
    assert updated_project.status_code == 200 and updated_project.json()["status"] == "completed"
    task = client.post(f"/api/v1/projects/{project_id}/tasks", headers=headers, json={"title": "Ship API", "description": "Complete backend API", "priority": "high"})
    assert task.status_code == 201 and task.json()["priority"] == "high"
    task_id = task.json()["task_id"]
    assert client.patch(f"/api/v1/tasks/{task_id}", headers=headers, json={"status": "in_progress"}).status_code == 200
    assert client.post(f"/api/v1/tasks/{task_id}/comments", headers=headers, json={"content": "Started"}).status_code == 201
    archived = client.post(f"/api/v1/projects/{project_id}/archive", headers=headers)
    assert archived.status_code == 200 and archived.json()["status"] == "archived"
    assert client.patch(f"/api/v1/projects/{project_id}", headers=headers, json={"name": "Should not change"}).status_code == 409
    assert client.post(f"/api/v1/projects/{project_id}/tasks", headers=headers, json={"title": "Should fail"}).status_code == 409


def test_project_members_and_task_collaboration(client):
    owner_headers = auth_headers(client, "owner@acme.test", "password123")
    projects = client.get("/api/v1/projects", headers=owner_headers).json()
    project_id = projects[0]["project_id"]
    member = client.get("/api/v1/users", headers=owner_headers).json()
    member_id = next(u["user_id"] for u in member if u["email"] == "member@acme.test")
    added = client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"user_id": member_id})
    assert added.status_code == 201
    members = client.get(f"/api/v1/projects/{project_id}/members", headers=owner_headers).json()
    assert any(u["user_id"] == member_id for u in members)

    # The project used above is archived by the previous test, so create a fresh project for collaboration.
    project = client.post("/api/v1/projects", headers=owner_headers, json={"name": "Collaboration Project"}).json()
    project_id = project["project_id"]
    assert client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"user_id": member_id}).status_code == 201
    task = client.post(f"/api/v1/projects/{project_id}/tasks", headers=owner_headers, json={"title": "Team task", "assignee_id": member_id, "collaborator_ids": [member_id], "priority": "medium"})
    assert task.status_code == 201
    assert member_id in task.json()["collaborator_ids"]
    task_id = task.json()["task_id"]
    changed = client.put(f"/api/v1/tasks/{task_id}/collaborators", headers=owner_headers, json={"user_ids": []})
    assert changed.status_code == 200 and changed.json()["collaborator_ids"] == []


def test_member_cannot_create_task(client):
    member_headers = auth_headers(client, "member@acme.test", "password123")
    projects = client.get("/api/v1/projects", headers=auth_headers(client, "owner@acme.test", "password123")).json()
    project_id = next(p["project_id"] for p in projects if p["name"] == "Collaboration Project")
    assert client.post(f"/api/v1/projects/{project_id}/tasks", headers=member_headers, json={"title": "Should fail"}).status_code == 403


def test_cross_tenant_project_isolation(client):
    response = client.post("/api/v1/auth/register", json={"tenant_name": "Other Tenant", "full_name": "Other Owner", "email": "owner@other.test", "password": "password123"})
    assert response.status_code == 201
    headers = auth_headers(client, "owner@other.test", "password123")
    projects = client.get("/api/v1/projects", headers=headers)
    assert projects.status_code == 200 and projects.json() == []
