# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
ErrorTracker — Multi-layer error tracking for device provider operations.

Tracks errors through execution layers so debugging is straightforward:
  Layer 1: Provider       — which provider type was used
  Layer 2: Transport      — API/SSH/serial connection issues
  Layer 3: Command        — individual device command that failed
  Layer 4: Mapper         — data translation issues
  Layer 5: Sync           — sync-level conflicts and failures

Each operation gets a unique trace_id and records timing + context
at every layer boundary. Errors are stored in both Frappe's Error Log
and the MikroTik Sync Log DocType for operational visibility.
"""

from __future__ import annotations

import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import frappe
from frappe.utils import now_datetime


@dataclass
class LayerSpan:
    """A single execution span within a traced operation."""

    layer: str
    operation: str
    start_time: float
    end_time: float = 0.0
    status: str = "running"      # running | success | error
    error_message: str = ""
    error_type: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    children: List["LayerSpan"] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000

    def to_dict(self) -> dict:
        return {
            "layer": self.layer,
            "operation": self.operation,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "details": self.details,
            "children": [c.to_dict() for c in self.children],
        }


class OperationTrace:
    """Full trace of a multi-layer operation.

    Captures the complete execution path from the Frappe controller
    down through the provider, transport, and device layers.
    """

    def __init__(self, operation: str, box_name: str = "", provider_type: str = ""):
        self.trace_id = str(uuid.uuid4())[:12]
        self.operation = operation
        self.box_name = box_name
        self.provider_type = provider_type
        self.start_time = time.time()
        self.status = "running"
        self.spans: List[LayerSpan] = []
        self._span_stack: List[LayerSpan] = []

    @property
    def duration_ms(self) -> float:
        return (time.time() - self.start_time) * 1000

    @property
    def has_errors(self) -> bool:
        return any(s.status == "error" for s in self.spans)

    @property
    def error_summary(self) -> str:
        """Get the deepest error message for user display."""
        errors = []
        self._collect_errors(self.spans, errors)
        if errors:
            return errors[-1]  # Deepest error
        return ""

    def _collect_errors(self, spans: List[LayerSpan], errors: list):
        for span in spans:
            if span.status == "error" and span.error_message:
                errors.append(f"[{span.layer}:{span.operation}] {span.error_message}")
            self._collect_errors(span.children, errors)

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "operation": self.operation,
            "box_name": self.box_name,
            "provider_type": self.provider_type,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 2),
            "spans": [s.to_dict() for s in self.spans],
        }


class ErrorTracker:
    """Singleton error tracker for device provider operations.

    Usage:
        tracker = ErrorTracker.instance()

        with tracker.trace("sync_interfaces", box_name="router1") as trace:
            with trace.span("provider", "connect"):
                provider.connect()
            with trace.span("command", "get_interfaces"):
                interfaces = provider.get_interfaces()

        # trace automatically logged on exit
    """

    _instance: Optional["ErrorTracker"] = None

    def __init__(self):
        self._active_traces: Dict[str, OperationTrace] = {}

    @classmethod
    def instance(cls) -> "ErrorTracker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @contextmanager
    def trace(
        self,
        operation: str,
        box_name: str = "",
        provider_type: str = "",
        auto_log: bool = True,
    ):
        """Start a new traced operation.

        Args:
            operation: Operation name (e.g. "sync_interfaces", "push_firewall")
            box_name: Arrowz Box name
            provider_type: Provider type (e.g. "mikrotik", "linux")
            auto_log: Automatically log to Frappe on completion

        Yields:
            TracedOperation context with .span() method
        """
        trace = OperationTrace(operation, box_name, provider_type)
        self._active_traces[trace.trace_id] = trace
        ctx = TracedOperation(trace)

        try:
            yield ctx
            trace.status = "error" if trace.has_errors else "success"
        except Exception as e:
            trace.status = "error"
            # Record the top-level exception if not already captured in a span
            if not trace.has_errors:
                span = LayerSpan(
                    layer="unhandled",
                    operation=operation,
                    start_time=trace.start_time,
                )
                span.end_time = time.time()
                span.status = "error"
                span.error_message = str(e)
                span.error_type = type(e).__name__
                span.details["traceback"] = traceback.format_exc()
                trace.spans.append(span)
            raise
        finally:
            self._active_traces.pop(trace.trace_id, None)
            if auto_log:
                self._log_trace(trace)

    def _log_trace(self, trace: OperationTrace):
        """Log a completed trace to Frappe."""
        try:
            if trace.has_errors:
                frappe.log_error(
                    title=f"Arrowz Provider Error: {trace.operation}",
                    message=frappe.as_json(trace.to_dict()),
                )

            # Also log to MikroTik Sync Log if it exists and the op is sync-related
            if trace.box_name and "sync" in trace.operation.lower():
                self._log_to_sync_log(trace)

        except Exception:
            # Never fail on logging
            pass

    def _log_to_sync_log(self, trace: OperationTrace):
        """Log sync operation to MikroTik Sync Log DocType."""
        try:
            if not frappe.db.exists("DocType", "MikroTik Sync Log"):
                return

            frappe.get_doc({
                "doctype": "MikroTik Sync Log",
                "arrowz_box": trace.box_name,
                "operation": trace.operation,
                "trace_id": trace.trace_id,
                "status": "Success" if trace.status == "success" else "Failed",
                "duration_ms": round(trace.duration_ms, 2),
                "error_message": trace.error_summary,
                "details": frappe.as_json(trace.to_dict()),
                "timestamp": now_datetime(),
            }).insert(ignore_permissions=True)
        except Exception:
            pass

    def get_recent_errors(self, box_name: str = "", limit: int = 20) -> List[dict]:
        """Get recent error traces for a box."""
        filters = {"status": "Failed"}
        if box_name:
            filters["arrowz_box"] = box_name

        try:
            if frappe.db.exists("DocType", "MikroTik Sync Log"):
                return frappe.get_all(
                    "MikroTik Sync Log",
                    filters=filters,
                    fields=["name", "operation", "trace_id", "error_message",
                            "duration_ms", "timestamp"],
                    order_by="creation desc",
                    limit=limit,
                )
        except Exception:
            pass

        return []


class TracedOperation:
    """Context wrapper for an active operation trace.

    Provides .span() context manager for tracking individual
    execution layers within the operation.
    """

    def __init__(self, trace: OperationTrace):
        self._trace = trace

    @property
    def trace_id(self) -> str:
        return self._trace.trace_id

    @contextmanager
    def span(self, layer: str, operation: str, **extra_details):
        """Track a single execution span.

        Args:
            layer: Layer name ("provider", "transport", "command", "mapper", "sync")
            operation: Specific operation within the layer
            **extra_details: Additional context to record

        Usage:
            with traced_op.span("command", "get_interfaces") as s:
                result = api.path("interface")
                s.record("count", len(result))
        """
        span = LayerSpan(
            layer=layer,
            operation=operation,
            start_time=time.time(),
            details=extra_details,
        )

        # Nest under parent span if in a stack
        if self._trace._span_stack:
            self._trace._span_stack[-1].children.append(span)
        else:
            self._trace.spans.append(span)

        self._trace._span_stack.append(span)
        recorder = SpanRecorder(span)

        try:
            yield recorder
            span.status = "success"
        except Exception as e:
            span.status = "error"
            span.error_message = str(e)
            span.error_type = type(e).__name__
            if self._trace.provider_type:
                span.details["provider_type"] = self._trace.provider_type
            raise
        finally:
            span.end_time = time.time()
            self._trace._span_stack.pop()


class SpanRecorder:
    """Helper to record additional data within a span."""

    def __init__(self, span: LayerSpan):
        self._span = span

    def record(self, key: str, value: Any):
        """Record a key-value pair in the span details."""
        self._span.details[key] = value

    def record_command(self, command: str):
        """Record the exact command/API call being executed."""
        self._span.details["command"] = command

    def record_response(self, response: Any):
        """Record a truncated version of the response."""
        s = str(response)
        self._span.details["response_preview"] = s[:500] if len(s) > 500 else s
