"""Inject runtime dependencies; preserve the existing orchestration as one code path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from src.services.contracts import AnalysisRequest, AuditPort, PipelineResult, WorkflowPort

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class RunOptions(TypedDict, total=False):
    downloads: bool


@dataclass
class AnalysisService:
    workflow: WorkflowPort
    engine: Engine
    audit: AuditPort

    def analyze(self, request: AnalysisRequest) -> PipelineResult:
        # Lazy import keeps entrypoint inspection independent of models/database/UI.
        from src.services.pipeline import process_call

        options: RunOptions = {} if request.downloads else {"downloads": False}
        result = process_call(
            request.audio_file,
            request.caller_id,
            request.department,
            self.workflow,
            self.engine,
            self.audit,
            **options,
        )
        if not isinstance(result, PipelineResult):
            raise TypeError("Legacy pipeline returned an unsupported result")
        return result
