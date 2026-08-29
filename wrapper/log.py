"""Structured logging, graph-trace collection, and the @traced_node decorator.

Every component uses a named logger under the ``khaoai`` namespace so that
output is easy to grep/filter.  The GraphTrace / TraceStep dataclasses
accumulate execution telemetry per chat request, and the TRACE_BUFFER keeps
the last 20 runs available via ``/api/debug/last-run``.
"""
from __future__ import annotations

import functools
import logging
import os
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Structured formatter
# ---------------------------------------------------------------------------

class _Fmt(logging.Formatter):
    """[HH:MM:SS.ms] LEVEL  component | message"""

    def format(self, record: logging.LogRecord) -> str:
        ts = time.strftime("%H:%M:%S", time.localtime(record.created))
        ms = int((record.created % 1) * 1000)
        level = record.levelname.ljust(5)
        name = record.name.replace("khaoai.", "").ljust(8)
        try:
            msg = record.getMessage()
        except Exception:
            msg = str(record.msg)
        return f"[{ts}.{ms:03d}] {level}  {name} | {msg}"


def setup_logging(level: str = "INFO") -> None:
    """Call once at startup to configure the khaoai logger hierarchy.

    Supports multiple log levels:
      - Simple global level: ``LOG_LEVEL=INFO``
      - Comma-separated component overrides: ``LOG_LEVEL=INFO,graph=DEBUG,mocks=WARNING``
      - Dedicated env vars: ``LOG_LEVEL_GRAPH=DEBUG``, ``LOG_LEVEL_API=INFO``, etc.
    """
    # Ensure stdout handles unicode characters safely on Windows console
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Parse base level and any inline component overrides
    parts = [p.strip() for p in (level or "INFO").split(",") if p.strip()]
    base_level_str = parts[0] if parts else "INFO"
    if "=" in base_level_str or ":" in base_level_str:
        base_level_str = "INFO"  # default if first item was a component pair

    base_level = getattr(logging, base_level_str.upper(), logging.INFO)

    root = logging.getLogger("khaoai")
    if not root.handlers:
        root.setLevel(logging.DEBUG)  # allow children to control their own thresholds
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_Fmt())
        root.addHandler(handler)
        root.propagate = False

    # Set default level for all components
    for comp in ("api", "graph", "auth", "mocks"):
        logging.getLogger(f"khaoai.{comp}").setLevel(base_level)

    # Apply inline comma-separated overrides (e.g. graph=DEBUG or graph:DEBUG)
    for part in parts:
        sep = "=" if "=" in part else (":" if ":" in part else None)
        if sep:
            comp_name, comp_lvl = part.split(sep, 1)
            comp_name = comp_name.strip().lower()
            lvl_val = getattr(logging, comp_lvl.strip().upper(), None)
            if lvl_val is not None:
                logging.getLogger(f"khaoai.{comp_name}").setLevel(lvl_val)

    # Apply dedicated env vars if present (e.g. LOG_LEVEL_GRAPH=DEBUG)
    for comp in ("api", "graph", "auth", "mocks"):
        env_val = os.getenv(f"LOG_LEVEL_{comp.upper()}")
        if env_val:
            lvl_val = getattr(logging, env_val.strip().upper(), None)
            if lvl_val is not None:
                logging.getLogger(f"khaoai.{comp}").setLevel(lvl_val)


def get_logger(component: str) -> logging.Logger:
    """Return a logger scoped to ``khaoai.<component>``."""
    return logging.getLogger(f"khaoai.{component}")


# ---------------------------------------------------------------------------
# Graph-trace dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TraceStep:
    node: str
    entered_at: float = 0.0
    exited_at: float = 0.0
    duration_ms: float = 0.0
    input_keys: list[str] = field(default_factory=list)
    output_keys: list[str] = field(default_factory=list)
    output_summary: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node": self.node,
            "duration_ms": round(self.duration_ms, 1),
            "output_summary": self.output_summary,
            "error": self.error,
        }


@dataclass
class GraphTrace:
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    query: str = ""
    started_at: float = 0.0
    steps: list[TraceStep] = field(default_factory=list)
    path: list[str] = field(default_factory=list)
    total_duration_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "query": self.query,
            "total_duration_ms": round(self.total_duration_ms, 1),
            "path": self.path,
            "steps": [s.to_dict() for s in self.steps],
            "error": self.error,
        }


import contextvars

# Last-N trace ring buffer
TRACE_BUFFER: deque[GraphTrace] = deque(maxlen=20)

# ContextVar automatically propagates across asyncio tasks / LangGraph node coroutines
_current_trace_var: contextvars.ContextVar[GraphTrace | None] = contextvars.ContextVar(
    "current_trace", default=None
)


def set_current_trace(trace: GraphTrace) -> None:
    _current_trace_var.set(trace)


def get_current_trace() -> GraphTrace | None:
    return _current_trace_var.get()


def clear_current_trace() -> None:
    _current_trace_var.set(None)


# ---------------------------------------------------------------------------
# @traced_node decorator
# ---------------------------------------------------------------------------

_log = get_logger("graph")


def traced_node(
    node_name: str,
    summary_fn: Callable[[dict], dict[str, Any]] | None = None,
) -> Callable:
    """Decorator for LangGraph node functions.

    Wraps the node in enter/exit logging with timing, trace-step recording,
    and error capture.

    ``summary_fn`` is an optional callable that receives the node's return dict
    and produces a compact summary dict for the trace (e.g. ``{"intent": "food_query"}``).
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(state: dict) -> dict:
            trace = get_current_trace()
            step_num = (len(trace.steps) + 1) if trace else "?"
            total_nodes = 5  # known graph size

            _log.info("|-- [%s/%s] %-22s >> ENTER", step_num, total_nodes, node_name)
            t0 = time.perf_counter()

            step = TraceStep(node=node_name, entered_at=t0)

            try:
                result = await fn(state)
                elapsed = (time.perf_counter() - t0) * 1000
                step.exited_at = time.perf_counter()
                step.duration_ms = elapsed
                step.output_keys = list(result.keys()) if isinstance(result, dict) else []

                summary = {}
                if summary_fn and isinstance(result, dict):
                    try:
                        summary = summary_fn(result)
                    except Exception:
                        pass
                step.output_summary = summary

                summary_str = "  ".join(f"{k}={v}" for k, v in summary.items()) if summary else ""
                _log.info(
                    "|-- [%s/%s] %-22s [+] EXIT  (%dms)  %s",
                    step_num, total_nodes, node_name, int(elapsed), summary_str,
                )

                if trace:
                    trace.steps.append(step)
                    trace.path.append(node_name)

                return result

            except Exception as exc:
                elapsed = (time.perf_counter() - t0) * 1000
                step.exited_at = time.perf_counter()
                step.duration_ms = elapsed
                step.error = str(exc)

                _log.error(
                    "|-- [%s/%s] %-22s [x] FAILED  (%dms)  error=%s",
                    step_num, total_nodes, node_name, int(elapsed), exc,
                )

                if trace:
                    trace.steps.append(step)
                    trace.path.append(f"{node_name}[FAILED]")

                raise

        return wrapper
    return decorator
