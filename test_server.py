"""Quick automated verification for the single-server khaoAI architecture."""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
from fastapi.testclient import TestClient
from main import app
import json

def test_all():
    print("Testing khaoAI Single-Server Suite...")
    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/health")
        print(f"1. /health -> {res.status_code}: {res.json()}")
        assert res.status_code == 200

        # 2. Static frontend check
        res = client.get("/")
        print(f"2. / (frontend) -> {res.status_code}, HTML length: {len(res.text)}")
        assert res.status_code == 200
        assert "<title>khaoAI" in res.text

        # 3. Auth login (demo user)
        res = client.post("/api/auth/login", json={"email": "demo@khaoai.com", "password": "demo123"})
        print(f"3. /api/auth/login -> {res.status_code}: {res.json().get('user')}")
        assert res.status_code == 200
        token = res.json()["access_token"]

        # 4. Settings check
        res = client.get("/api/settings", headers={"Authorization": f"Bearer {token}"})
        print(f"4. /api/settings -> {res.status_code}: {res.json()}")
        assert res.status_code == 200

        # 5. Chat POST (orchestrates in-process LangGraph)
        print("5. Invoking /api/chat with fast-path greeting...")
        res = client.post("/api/chat", json={"message": "hi", "location": "Salt Lake, Sector V"})
        print(f"   /api/chat greeting -> {res.status_code}")
        print(f"   Reply: {res.json().get('reply')}")
        assert res.status_code == 200

        print("6. Invoking /api/chat with food query...")
        res = client.post("/api/chat", json={"message": "What should I eat now for dinner?", "location": "Salt Lake, Sector V"})
        data = res.json()
        print(f"   /api/chat food query -> {res.status_code}")
        print(f"   Reply: {data.get('reply')}")
        print(f"   Recommendations count: {len(data.get('recommendations', []))}")
        if data.get('recommendations'):
            top = data['recommendations'][0]
            print(f"   Top Pick: {top.get('name')} from {top.get('restaurant_name')} on {top.get('platform')} (₹{top.get('price')}, ⭐{top.get('rating')})")
        assert res.status_code == 200

        # 7. Debug last-run trace
        res = client.get("/api/debug/last-run")
        trace = res.json()
        print(f"7. /api/debug/last-run -> {res.status_code}")
        print(f"   Trace Path: {trace.get('path')}")
        print(f"   Total Duration: {trace.get('total_duration_ms')}ms")
        print(f"   Steps Count: {len(trace.get('steps', []))}")
        assert res.status_code == 200
        assert len(trace.get('steps', [])) > 0

    print("\n✅ All automated verification checks passed cleanly!")

if __name__ == "__main__":
    test_all()
