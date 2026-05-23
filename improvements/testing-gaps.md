# Testing Gaps

The project has a strong existing test suite: 109 unit and security tests pass cleanly on a fresh checkout in under 20 seconds. This document covers what is **not** tested and the riskiest gaps worth filling.

## Current Coverage Map

| Layer | Tests in | What is covered |
|---|---|---|
| Agents | `tests/unit/test_intake.py`, `tests/unit/test_transcription.py`, `tests/unit/test_summarization.py`, `tests/unit/test_qa_scoring.py`, `tests/unit/test_report.py` | Each agent's happy path plus a small set of edge cases. |
| Audio utils | `tests/unit/test_audio.py` | Format detection, validation rules, property extraction. |
| Graph | `tests/unit/test_edges.py`, `tests/unit/test_workflow_error.py` | Routing logic, error path. |
| State | `tests/unit/test_state.py` | Pydantic model validation. |
| Services | `tests/unit/test_history_service.py` | `list_calls` and `get_call_detail`. |
| Security | `tests/security/test_pii_detection.py`, `tests/security/test_prompt_injection.py` | PII patterns, injection patterns. |
| Integration | `tests/integration/test_database_persistence.py` | DB persistence end-to-end (no LLM). |
| Pipeline end-to-end | `tests/integration/test_pipeline_end_to_end.py` | Full pipeline (needs an LLM key). |

## Gaps By Risk

### TEST-01: LLM-mocked end-to-end pipeline test

- **Severity:** High value, low effort
- **What is missing:** The two tests in `tests/integration/test_pipeline_end_to_end.py` cover the full pipeline, but they require a real LLM key, so they are excluded from default CI. There is no fully-offline end-to-end test that catches integration regressions between nodes.

**Suggested addition.** Add `tests/integration/test_pipeline_offline.py` that:

- Uses the `db_engine` fixture from `tests/conftest.py:111-118`.
- Patches `src.utils.llm_factory.get_llm` to return a stub whose `.with_structured_output(...)` produces a `MagicMock` that returns canned `SummaryResult` and `QAScoreResult` instances.
- Patches `src.agents.transcription.run_transcription` (or feeds a pre-cached `TranscriptionResult` via the `TranscriptionCache` table) so Whisper does not need to run.
- Invokes the compiled workflow once and asserts the report's structure.

This becomes the new "smoke test" and can run in CI on every push.

### TEST-02: Routing decisions on critical compliance flags

- **Severity:** Medium value, small effort
- **What is missing:** `route_after_qa` at `src/graph/edges.py:20-24` returns `supervisor_review` whenever any `compliance_flag` has severity `critical`. This is exercised once in `tests/unit/test_edges.py` but the workflow integration is not.

**Suggested addition.** Add a test that builds a `PipelineState` with a stubbed `qa_scores` containing a critical flag and asserts the workflow ends in `supervisor_step` rather than `report_step`.

### TEST-03: PII redaction symmetry with intake metadata scan

- **Severity:** Medium value, small effort
- **What is missing:** `src/agents/intake.py:19-24` and `src/security/pii_redactor.py:22-31` have similar but non-identical patterns (see `code-review.md#cr-08`). There is no test asserting that PII detected in metadata is also redacted by the main redactor, or vice versa.

**Suggested addition.** Parametrize the existing PII detection tests at `tests/security/test_pii_detection.py` over a shared list of cases and run both functions against each. Failures highlight the asymmetry.

### TEST-04: Transcription cache hit and miss

- **Severity:** Medium value, small effort
- **What is missing:** The cache helpers `_check_cache` and `_save_cache` at `src/agents/transcription.py:121-164` are not directly tested. The behavior is implicit in the end-to-end tests, which are skipped in CI.

**Suggested addition.** Add a unit test that:

1. Builds a `TranscriptionResult` and calls `_save_cache` with a known hash.
2. Calls `_check_cache` with the same hash and asserts the round-trip is byte-identical.
3. Calls `_check_cache` with a different hash and asserts `None`.

### TEST-05: Empty audio and oversized audio at the workflow boundary

- **Severity:** Medium value, small effort
- **What is missing:** `tests/unit/test_intake.py` covers individual validation paths, but the workflow's response to a failed intake is only partially covered in `tests/unit/test_workflow_error.py`.

**Suggested addition.** Add tests that submit an empty `audio_data=b""` and a 51-MB byte string. Assert in both cases that the workflow terminates in `error_step` and the message in `state["error"]` is informative.

### TEST-06: Speaker diarization edge cases

- **Severity:** Medium value, small effort
- **What is missing:** The heuristic `SpeakerDiarizer` at `src/agents/transcription.py:64-102` has logic for first-segment selection, gap-based speaker change, question-followed-by-answer, and short-affirmation rules. Only a couple of these are tested.

**Suggested addition.** A `parametrize`d test over short hand-crafted segment lists with the expected speaker assignment. Each rule should have at least one positive and one negative case.

### TEST-07: Report PDF generation does not crash on minimal data

- **Severity:** Low value, small effort
- **What is missing:** `generate_report_pdf` at `src/agents/report.py:73-119` is partially exercised in `tests/unit/test_report.py`, but not against a report with no compliance flags and an empty `entities` list. Pydantic permits both.

**Suggested addition.** A test that constructs the minimal valid `CallReport` and asserts `generate_report_pdf` returns at least 1 KB of bytes that start with `b"%PDF"`.

### TEST-08: AuditLogger does not raise when DB write fails

- **Severity:** Low value, small effort
- **What is missing:** `src/security/audit.py:23-32` writes directly to the DB. There is no test that a failure inside `session_scope` propagates up to the caller (which is what we want, but it should be asserted).

**Suggested addition.** Patch `session.add` to raise and assert the error surfaces.

## CI Recommendations

The `.github/workflows/ci.yml` proposed by this audit runs the unit and security suites by default and skips integration. To extend coverage in CI without exposing API keys:

1. Implement TEST-01 (offline end-to-end with mocked LLMs). The new test would run in the default CI matrix.
2. Add a separate workflow gated on `workflow_dispatch` that runs `tests/integration/test_pipeline_end_to_end.py` with `OPENAI_API_KEY` available as a repository secret. This becomes a manually-triggered smoke check before tagging a release.

## Anti-Goals

The suite is intentionally fast (under 20 seconds). Adding flaky network-dependent tests, real Whisper invocations on real audio, or large fixture files would erode that. Stick to mocks and pure unit tests for anything that touches an LLM or a downloaded model.
