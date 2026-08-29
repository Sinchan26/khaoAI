"""Database-backed smoke test. Requires a disposable PostgreSQL DATABASE_URL."""
from __future__ import annotations

import uuid
from fastapi.testclient import TestClient
from main import app


def test_all() -> None:
    email = f"smoke-{uuid.uuid4().hex[:10]}@example.com"
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["provider"] == "swiggy-read-only"

        register = client.post("/api/auth/register", json={
            "email": email, "password": "StrongPass123!", "display_name": "Smoke Test",
        })
        assert register.status_code == 201, register.text
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/settings", headers=headers).status_code == 200
        assert client.get("/api/debug/traces").status_code == 401
    print("Smoke checks passed")


if __name__ == "__main__":
    test_all()
