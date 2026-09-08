import os
from pathlib import Path

DB_PATH = Path("test_aegis.db")
if DB_PATH.exists(): DB_PATH.unlink()
os.environ["DATABASE_URL"] = "sqlite:///./test_aegis.db"
os.environ["JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client: yield test_client

def auth_headers(client, email, password):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

def test_registration_login_health_and_tenant_verification(client):
    response = client.post("/api/v1/auth/register", json={"tenant_name":"Acme Test","full_name":"Owner User","email":"owner@acme.test","password":"password123"})
    assert response.status_code == 201
    assert client.get("/health").json()["status"] == "ok"
    tenant = client.get("/api/v1/tenant", headers=auth_headers(client,"owner@acme.test","password123"))
    assert tenant.status_code == 200 and all(tenant.json()["verification"].values())

def test_owner_can_add_users_and_roles_are_enforced(client):
    headers = auth_headers(client,"owner@acme.test","password123")
    member = client.post("/api/v1/users", headers=headers, json={"full_name":"Member User","email":"member@acme.test","password":"password123","role":"Member"})
    admin = client.post("/api/v1/users", headers=headers, json={"full_name":"Admin User","email":"admin@acme.test","password":"password123","role":"Admin"})
    assert member.status_code == 201 and member.json()["role"] == "Member"
    assert admin.status_code == 201 and admin.json()["role"] == "Admin"
    assert client.post("/api/v1/projects", headers=auth_headers(client,"member@acme.test","password123"), json={"name":"Denied"}).status_code == 403

def test_owner_can_change_workspace_roles_but_members_cannot(client):
    owner = auth_headers(client,"owner@acme.test","password123")
    users = client.get("/api/v1/users", headers=owner).json()
    member_id = next(u["user_id"] for u in users if u["email"] == "member@acme.test")
    changed = client.patch(f"/api/v1/users/{member_id}", headers=owner, json={"role":"Admin"})
    assert changed.status_code == 200 and changed.json()["role"] == "Admin"
    assert client.patch(f"/api/v1/users/{member_id}", headers=auth_headers(client,"admin@acme.test","password123"), json={"role":"Member"}).status_code == 403
    restored = client.patch(f"/api/v1/users/{member_id}", headers=owner, json={"role":"Member"})
    assert restored.status_code == 200 and restored.json()["role"] == "Member"

def test_project_lifecycle_and_task_flow(client):
    headers = auth_headers(client,"owner@acme.test","password123")
    project = client.post("/api/v1/projects", headers=headers, json={"name":"Aegis MVP","description":"Secure multi-tenant project"})
    assert project.status_code == 201
    project_id = project.json()["project_id"]
    updated = client.patch(f"/api/v1/projects/{project_id}", headers=headers, json={"name":"Aegis Production MVP","description":"Production-ready secure workspace","status":"completed"})
    assert updated.status_code == 200 and updated.json()["status"] == "completed"
    task = client.post(f"/api/v1/projects/{project_id}/tasks", headers=headers, json={"title":"Ship API","description":"Complete backend API","priority":"high"})
    assert task.status_code == 201 and task.json()["priority"] == "high"
    task_id = task.json()["task_id"]
    assert client.patch(f"/api/v1/tasks/{task_id}", headers=headers, json={"status":"in_progress"}).status_code == 200
    assert client.post(f"/api/v1/tasks/{task_id}/comments", headers=headers, json={"content":"Started"}).status_code == 201
    assert client.post(f"/api/v1/projects/{project_id}/archive", headers=headers).status_code == 200
    assert client.patch(f"/api/v1/projects/{project_id}", headers=headers, json={"name":"Should not change"}).status_code == 409
    assert client.post(f"/api/v1/projects/{project_id}/tasks", headers=headers, json={"title":"Should fail"}).status_code == 409

def test_project_members_and_task_collaboration(client):
    owner = auth_headers(client,"owner@acme.test","password123")
    users = client.get("/api/v1/users", headers=owner).json()
    member_id = next(u["user_id"] for u in users if u["email"] == "member@acme.test")
    project = client.post("/api/v1/projects", headers=owner, json={"name":"Collaboration Project"}).json()
    project_id = project["project_id"]
    assert client.post(f"/api/v1/projects/{project_id}/members", headers=owner, json={"user_id":member_id}).status_code == 201
    task = client.post(f"/api/v1/projects/{project_id}/tasks", headers=owner, json={"title":"Team task","assignee_id":member_id,"collaborator_ids":[member_id],"priority":"medium"})
    assert task.status_code == 201 and member_id in task.json()["collaborator_ids"]
    task_id = task.json()["task_id"]
    changed = client.put(f"/api/v1/tasks/{task_id}/collaborators", headers=owner, json={"user_ids":[]})
    assert changed.status_code == 200 and changed.json()["collaborator_ids"] == []

def test_member_cannot_create_task(client):
    member_headers = auth_headers(client,"member@acme.test","password123")
    project_id = next(p["project_id"] for p in client.get("/api/v1/projects", headers=auth_headers(client,"owner@acme.test","password123")).json() if p["name"] == "Collaboration Project")
    assert client.post(f"/api/v1/projects/{project_id}/tasks", headers=member_headers, json={"title":"Should fail"}).status_code == 403

def test_cross_tenant_project_isolation(client):
    response = client.post("/api/v1/auth/register", json={"tenant_name":"Other Tenant","full_name":"Other Owner","email":"owner@other.test","password":"password123"})
    assert response.status_code == 201
    projects = client.get("/api/v1/projects", headers=auth_headers(client,"owner@other.test","password123"))
    assert projects.status_code == 200 and projects.json() == []
