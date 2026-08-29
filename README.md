# khaoAI 🍽️ — Agentic Food Concierge

**khaoAI** is a lightweight, single-server AI food recommendation assistant built with **FastAPI**, **LangGraph**, and **ChatOpenAI**. When a user asks natural language questions like *"What should I eat now?"* or *"Suggest some veg biryani under ₹200"*, khaoAI analyzes live context and searches across food delivery platforms (**Tomato 🍅** and **Twiggy 🌿**) to recommend the cheapest, highest-rated, and fastest delivery options.

---

## ⚡ Architecture Highlights

Consolidated into a **single FastAPI process** following the UCP-Funnel pattern:
- **One Server, One Port (`8000`)**: Serves the modern static chat frontend at `/` and all API/WebSocket endpoints under `/api/`.
- **In-Process LangGraph Agent**: Executes graph nodes directly in-process without multi-service latency or Azure Functions overhead.
- **In-Memory Platform Mocks**: Tomato 🍅 and Twiggy 🌿 synthetic datasets (100 restaurants, 1,500 menu items) loaded once into memory at startup.
- **Verbose Graph Tracing**: Live arrow-chain execution paths, per-node timing in milliseconds, step output summaries, and `/api/debug/last-run` endpoints.

```
One Command: uvicorn main:app --port 8000 --reload

├── /api/chat        → REST + WebSocket chat (direct in-process LangGraph execution)
├── /api/auth        → JWT user authentication (register, login, session)
├── /api/settings    → User dietary, budget & location preferences
├── /api/debug       → Real-time graph execution telemetry (/last-run & /traces)
├── /health          → Health check endpoint
│
├── In-Memory Mocks  → Tomato 🍅 & Twiggy 🌿 catalogs (zero HTTP overhead)
├── LangGraph Graph  → 5-node pipeline with @traced_node telemetry
└── / (Static UI)    → Premium dark-mode HTML/CSS/JS chat with live trace viewer
```

---

## 🧠 LangGraph Agent Pipeline

```
START
  ↓
[intent_classifier]  ──(general_chat)──→ [response_formatter] ──→ END
  ↓ (food_query)                                 ↑
[context_resolver]                               │
  ↓                                              │
[food_searcher]  ──→ [ranker] ───────────────────┘
```

1. **`intent_classifier`**: Fast deterministic regex for greetings (sub-millisecond) + ChatOpenAI fallback for intent/entity extraction.
2. **`context_resolver`**: Detects current meal window (Breakfast, Lunch, Evening Snacks, Dinner, Late Night) and resolves target location.
3. **`food_searcher`**: Queries in-memory Tomato 🍅 and Twiggy 🌿 catalogs concurrently with keyword, cuisine, budget, and dietary filters.
4. **`ranker`**: Computes normalized composite scores:
   $$\text{Score} = 0.40 \times \text{Price}_{\text{inv}} + 0.30 \times \text{Rating} + 0.30 \times \text{Delivery}_{\text{inv}}$$
   Assigns dynamic badges: `Cheapest Pick`, `Top Rated` (⭐ $\ge 4.7$), and `Superfast Delivery` ($\le 20$ mins).
5. **`response_formatter`**: Generates a friendly, conversational foodie summary with highlighted top picks.

---

## 🔍 Robust Logging & Verbose Graph Tracing

Every request is logged to the console with structured timestamps, component tags, and correlation IDs:

```text
[21:47:52.956] INFO   api      | [>] Chat request received  (request_id=d3860fb1f7ab, query='What should I eat now for dinner?')
[21:47:52.957] INFO   graph    | /-- Graph START  (request_id=d3860fb1f7ab)
[21:47:52.961] INFO   graph    | |-- [1/5] intent_classifier      >> ENTER
[21:47:52.975] INFO   graph    | |-- [1/5] intent_classifier      [+] EXIT  (14ms)  intent=food_query  entities=none
[21:47:52.976] INFO   graph    | |-- Route: intent_classifier -> context_resolver  (condition: intent=food_query)
[21:47:52.977] INFO   graph    | |-- [2/5] context_resolver       >> ENTER
[21:47:52.977] INFO   graph    | |-- [2/5] context_resolver       [+] EXIT  (0ms)  meal_type=dinner  location=Salt Lake, Sector V
[21:47:52.979] INFO   graph    | |-- [3/5] food_searcher          >> ENTER
[21:47:52.980] INFO   graph    | │  └─ Searching Tomato (location=Salt Lake, Sector V, meal=dinner, query=None)
[21:47:52.982] INFO   graph    | │  └─ Searching Twiggy (location=Salt Lake, Sector V, meal=dinner, query=None)
[21:47:52.984] INFO   graph    | |-- [3/5] food_searcher          [+] EXIT  (5ms)  tomato_hits=20  twiggy_hits=20  total=40
[21:47:52.986] INFO   graph    | |-- [4/5] ranker                 >> ENTER
[21:47:52.987] INFO   graph    | |-- [4/5] ranker                 [+] EXIT  (0ms)  top_pick=Yellow Dal Tadka with Kashmiri Pulao ₹175 ⭐5.0  ranked=6
[21:47:52.988] INFO   graph    | |-- [5/5] response_formatter     >> ENTER
[21:47:53.481] INFO   graph    | |-- [5/5] response_formatter     [+] EXIT  (492ms)  reply_len=297  has_reply=True
[21:47:53.482] INFO   graph    | \-- Graph END  [+]  (525ms)  path=[intent_classifier -> context_resolver -> food_searcher -> ranker -> response_formatter]
[21:47:53.482] INFO   api      | [<] Chat response sent  (request_id=d3860fb1f7ab, recommendations=6)
```

### Debug API Endpoints
- **`GET /api/debug/last-run`**: Inspect the JSON telemetry of the most recent graph execution (nodes visited, duration in ms, error status, step summaries).
- **`GET /api/debug/traces`**: Ring buffer containing the last 20 graph execution traces.

---

## 📁 Repository Structure

```
khaoAI/
├── main.py                     # Single FastAPI application entry point
├── requirements.txt            # Unified dependencies file
├── test_server.py              # Automated test suite
├── .env.example                # Environment variables template
│
├── frontend/                   # Modern Vanilla Dark Chat UI (Served at /)
│   ├── index.html              # Single page layout (Auth, Chat, Modals)
│   ├── style.css               # HSL color system, glassmorphism, animations
│   └── app.js                  # WebSocket client, streaming tokens, food cards
│
├── wrapper/                    # Application layer (API, Agent, Auth)
│   ├── log.py                  # Structured logging, GraphTrace & @traced_node
│   ├── models.py               # Pydantic v2 schemas (Auth, Chat, Food DTO)
│   ├── prompts.py              # Intent and Response system prompts
│   ├── auth.py                 # JWT security, password hashing & auth middleware
│   ├── state.py                # In-memory session state management
│   ├── llm.py                  # OpenAI config, LangGraph builder & orchestrate()
│   ├── routes/
│   │   ├── auth.py             # POST /api/auth/register, /api/auth/login, /api/auth/me
│   │   ├── chat.py             # POST /api/chat & WS /api/chat/ws/{session_id}
│   │   ├── config.py           # GET & PUT /api/settings
│   │   └── debug.py            # GET /api/debug/last-run & /api/debug/traces
│   └── graph/
│       ├── state.py            # FoodAgentState TypedDict
│       └── nodes.py            # All 5 graph nodes wrapped with @traced_node
│
├── mocks/                      # In-process food delivery simulators
│   └── store.py                # In-memory Tomato + Twiggy data store & filtering
│
├── db/                         # Database resources
│   └── migrations/
│       └── 001_init.sql        # Optional PostgreSQL schema for persistence
│
└── platform/                   # Preserved original microservice blueprints
```

---

## 🚀 Getting Started

### 1. Installation

Clone repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
OPENAI_API_KEY=sk-proj-your-openai-api-key   # Optional: fallback heuristics included if omitted
OPENAI_MODEL=gpt-4o-mini
JWT_SECRET_KEY=khaoai-super-secret-key-2026
DEFAULT_LOCATION=Salt Lake, Sector V

# Log Level Options:
LOG_LEVEL=INFO                                      # Simple global level
# LOG_LEVEL=INFO,graph=DEBUG,mocks=WARNING,api=INFO # Multi-level / per-component overrides
# LOG_LEVEL_GRAPH=DEBUG                             # Dedicated component env var
```

### 3. Run Application

Start the server:
```bash
uvicorn main:app --port 8000 --reload
```

Open your browser at:
```
http://localhost:8000
```

- **Demo Account**: `demo@khaoai.com` / `demo123` (or register any new account)

---

## 🧪 Automated Testing

Run the automated end-to-end verification suite:
```bash
python test_server.py
```

This verifies:
1. `/health` check
2. Static frontend delivery at `/`
3. User login & JWT validation
4. User settings retrieval
5. Fast-path intent routing (greeting in $<30$ms)
6. Multi-platform search & ranking with composite scoring
7. `/api/debug/last-run` trace generation
