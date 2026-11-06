"""Internal typed-report adapter for a future authenticated HTTP route."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.services.contracts import AnalysisError, AnalysisPort, AnalysisRequest

if TYPE_CHECKING:
    from src.graph.state import CallReport


def analyze_call(service: AnalysisPort, request: AnalysisRequest) -> CallReport:
    result = service.analyze(request)
    if not result.success or result.report is None:
        raise AnalysisError(result.error or "Analysis produced no report")
    return result.report
