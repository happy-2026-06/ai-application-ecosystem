"""Authentication tests: register, login, token refresh, password change."""
import pytest


async def test_register_success(client):
    resp = await client.post("/api/auth/register", json={"username": "newuser1", "password": "test1234"})
    assert resp.status_code == 201
    assert resp.json()["username"] == "newuser1"


async def test_register_duplicate(client):
    await client.post("/api/auth/register", json={"username": "dup1", "password": "123456"})
    resp = await client.post("/api/auth/register", json={"username": "dup1", "password": "123456"})
    assert resp.status_code == 409


async def test_register_short_password(client):
    resp = await client.post("/api/auth/register", json={"username": "x1", "password": "12"})
    assert resp.status_code == 422


async def test_login_admin(client):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


async def test_login_nonexistent(client):
    resp = await client.post("/api/auth/login", json={"username": "nobody", "password": "123456"})
    assert resp.status_code == 401


async def test_me_authenticated(client, admin_headers):
    resp = await client.get("/api/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


async def test_me_no_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_change_password_ok(client, admin_headers):
    resp = await client.post("/api/auth/change-password", json={
        "old_password": "123456", "new_password": "newpass123"
    }, headers=admin_headers)
    assert resp.status_code == 200


async def test_change_wrong_old(client, admin_headers):
    resp = await client.post("/api/auth/change-password", json={
        "old_password": "wrongold", "new_password": "newpass123"
    }, headers=admin_headers)
    assert resp.status_code == 400
