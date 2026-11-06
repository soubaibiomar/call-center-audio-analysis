"""Lightweight application contracts; importing them performs no runtime setup."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from src.graph.state import CallReport


@dataclass(frozen=True)
class AnalysisRequest:
    """Trusted local audio path and optional metadata, independent of any UI."""

    audio_file: str | Path | None
    caller_id: str | None = None
    department: str | None = None
    downloads: bool = True


@dataclass
class PipelineResult:
    """Preserve legacy fields and expose the same typed report to other callers."""

    success: bool
    transcript: str = ""
    summary_md: str = ""
    qa_md: str = ""
    json_path: str | None = None
    pdf_path: str | None = None
    error: str | None = None
    report: CallReport | None = None


class AnalysisPort(Protocol):
    def analyze(self, request: AnalysisRequest) -> PipelineResult: ...


class WorkflowPort(Protocol):
    """LangGraph's dynamic state boundary; report validation stays in the pipeline."""

    def invoke(self, input: Any) -> Mapping[str, Any]: ...


class AuditPort(Protocol):
    def log(
        self, call_id: str, action: str, user: str, details: dict[str, object] | None = None
    ) -> None: ...


class AnalysisError(RuntimeError):
    """An internal analysis failure for a transport to translate into its own errors."""
