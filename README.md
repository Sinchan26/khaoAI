# khaoAI — Swiggy Food Ranking Assistant

khaoAI is a lightweight, single-process FastAPI and LangGraph application that
searches the official Swiggy Food MCP server and ranks live menu items using
price, rating, availability, and persisted user preferences.

The current application is recommendation-only. Cart, payment, confirmation,
and order-placement tools are blocked by a deterministic allowlist in
`wrapper/providers/swiggy.py`.

## Active architecture

```text
Browser
  ├─ JWT auth and persistent settings
  ├─ Swiggy OAuth 2.1 + PKCE
  └─ REST/WebSocket chat
          │
          ▼
FastAPI :8000
  ├─ PostgreSQL: users, settings, sessions, messages, provider connections
  ├─ LangGraph: intent → context → Swiggy search → rank → response
  ├─ Swiggy MCP read-only client
  └─ Static frontend
```

### Repository layout

```text
main.py
frontend/                       Active vanilla frontend
wrapper/
  db.py                         Async SQLAlchemy engine
  db_models.py                  Persistent entities
  auth.py                       Argon2 + JWT authentication
  providers/swiggy.py           OAuth, encrypted token, MCP, normalizer/cache
  graph/                        LangGraph state and nodes
  routes/                       Auth, settings, chat, debug, provider routes
db/alembic/                     PostgreSQL migrations
mocks/data/                     20 small deterministic test fixtures only
tests/                          Provider safety, normalization, ranking tests
legacy/                         Archived Azure services and former React studio
```

Nothing under `legacy/` is imported by the active application.

## Implemented phases 1–5

1. PostgreSQL persistence, Alembic, Argon2 passwords, JWT authentication, and
   per-user session ownership.
2. Swiggy OAuth with PKCE, encrypted access-token storage, expiration handling,
   saved-address selection, and a read-only MCP client.
3. Live `search_menu` integration, Swiggy response normalization, hard filters,
   preference-aware ranking, and recommendation snapshots in chat messages.
4. Persistent chat history restored into LangGraph with a user/session thread ID.
5. MCP retries, short-lived cache, safe provider errors, protected debug/history
   endpoints, browser-output escaping, compact fixtures, and automated tests.

## Setup

### 1. Create environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

On Linux/macOS, activate with `source .venv/bin/activate` and copy with
`cp .env.example .env`.

Generate the token-encryption key shown in `.env.example` and set a strong,
random `JWT_SECRET_KEY`.

### 2. Start PostgreSQL and migrate

Start the included local PostgreSQL service (or use an existing PostgreSQL
instance), confirm `DATABASE_URL`, then migrate:

```bash
docker compose up -d postgres
alembic upgrade head
```

Keep `AUTO_CREATE_TABLES=false` and use Alembic so schema history remains
consistent. The flag exists only for isolated throwaway tests.

### 3. Run

```bash
uvicorn main:app --port 8000 --reload
```

Open `http://localhost:8000`, register a khaoAI account, open Settings, connect
Swiggy using phone/OTP, and choose one of the addresses returned by Swiggy.

Swiggy currently uses five-day access tokens without refresh-token support. A
401 or expiry requires reconnecting through Settings.

## Safe tool boundary

Allowed MCP tools:

- `get_addresses`
- `search_menu`
- `search_restaurants`
- `get_restaurant_menu`

Blocked categories include cart modification, coupons, payment, confirmation,
checkout, ordering, cancellation, and tracking. Adding any new tool requires a
code review and an explicit change to `READ_ONLY_TOOLS`.

## Tests

Unit tests never call live Swiggy:

```bash
pytest -q
```

The database smoke test requires a disposable PostgreSQL database:

```bash
python test_server.py
```

Live OAuth verification is intentionally manual because it requires the user's
Swiggy phone/OTP consent and a saved delivery address.
