"""Debug routes for inspecting graph traces and execution telemetry."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from wrapper.auth import require_current_user
from wrapper.config import settings
from wrapper.log import TRACE_BUFFER
from wrapper.models import UserProfile

router = APIRouter(prefix="/debug", tags=["Debug"])


def _user_traces(user_id: str):
    if not settings.debug_endpoints_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return [trace for trace in TRACE_BUFFER if trace.owner_user_id == user_id]


@router.get("/last-run")
def get_last_graph_trace(user: UserProfile = Depends(require_current_user)):
    """Return the most recent graph execution trace for debugging."""
    traces = _user_traces(user.id)
    if not traces:
        return {"message": "No graph traces recorded yet", "steps": []}
    return traces[-1].to_dict()


@router.get("/traces")
def get_all_graph_traces(user: UserProfile = Depends(require_current_user)):
    """Return all buffered graph traces (last 20)."""
    return [trace.to_dict() for trace in _user_traces(user.id)]
