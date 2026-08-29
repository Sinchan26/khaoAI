"""Debug routes for inspecting graph traces and execution telemetry."""
from __future__ import annotations

from fastapi import APIRouter
from wrapper.log import TRACE_BUFFER

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/last-run")
def get_last_graph_trace():
    """Return the most recent graph execution trace for debugging."""
    if not TRACE_BUFFER:
        return {"message": "No graph traces recorded yet", "steps": []}
    return TRACE_BUFFER[-1].to_dict()


@router.get("/traces")
def get_all_graph_traces():
    """Return all buffered graph traces (last 20)."""
    return [t.to_dict() for t in TRACE_BUFFER]
