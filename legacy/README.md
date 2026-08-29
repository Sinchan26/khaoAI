# Legacy architecture

This directory contains code from the original Azure-oriented, multi-service
version of khaoAI. It is preserved for reference and is not imported or started
by the active single-process FastAPI application.

## Contents

- `azure_microservices/platform/`: Azure Functions for the API, LangGraph
  agent, MCP tools, and Tomato/Twiggy simulator services.
- `react_studio/studio/`: the former React/Vite frontend.

The active application lives at the repository root in `main.py`, `wrapper/`,
`frontend/`, and `mocks/`. Active mock datasets were moved to `mocks/data/` so
the current runtime does not depend on archived code.

Do not add new features here. New implementation work should target the active
single-server architecture.
