# Tech Debt and Refactoring

Structural and maintainability observations, sorted by value over effort. None of these block release. The project is in good shape; this list is the "next two months of incremental cleanup" backlog, not a rewrite.

## High Value, Small Effort

### TD-01: Single source of truth for PII patterns

**Where:** `src/agents/intake.py:19-24` and `src/security/pii_redactor.py:22-31`.

Two slightly different SSN and phone patterns live in two files. The intake scanner runs first (on metadata), the redactor runs later (on transcript text). Drift between the two is invisible until a real call leaks PII.

**Fix.** Move the patterns into `src/security/pii_patterns.py` as a single typed list. Have both files import from it. Existing tests at `tests/security/test_pii_detection.py` and `tests/unit/test_intake.py` continue to pass without changes.

### TD-02: Extract transcript-segment formatting

**Where:** `src/agents/summarization.py:46-52`, `src/agents/qa_scoring.py:114-126`.

Both functions iterate `transcript.segments` and emit `[MM:SS-MM:SS] Speaker: text` lines. The format is identical except QA also appends a summary block. Duplication is fine today; the risk is divergent formatting if either is updated.

**Fix.** Add `format_transcript_segments(transcript)` to `src/utils/formatters.py`. Have both agents call it. Net change: about 30 lines moved.

### TD-03: Inline the duplicated `compile_report` calls

**Where:** `src/graph/workflow.py:148-187`.

`report_node` and `supervisor_review_node` differ only by status. See `code-review.md#cr-07`.

**Fix.** A small `_make_report(state, status)` helper at the top of the file.

### TD-04: Remove dead `_DEFAULT_DB_KEY`

**Where:** `src/utils/config.py:12-14`.

The auto-generated key is never used because the SQLCipher activation requires the env var. See `code-review.md#cr-04`.

**Fix.** Delete the constant and default `db_encryption_key` to `""`.

## Medium Value, Small Effort

### TD-05: Replace lambdas with `functools.partial`

**Where:** `src/graph/workflow.py:195, 198`.

Improves debugger traces; preserves function names in LangSmith. See `code-review.md#cr-05`.

### TD-06: Module-level globals to instance attributes

**Where:** `src/services/pipeline.py:19-20`, `src/agents/transcription.py:18-19`, `src/database/connection.py:42`.

Move into the factories that already exist. See `code-review.md#cr-02`. Behavior is identical; tests get cleaner.

### TD-07: Assert dimension weights sum to 1.0

**Where:** `src/agents/qa_scoring.py:18-24`.

One-line assertion. See `code-review.md#cr-03`.

### TD-08: Standardize logging across agents

The codebase mixes `print` (in `app.py:24, 26, 30`) and `logger.info(...)` (everywhere else). Use the logger throughout for consistency. `app.py` already configures logging at line 9.

## High Value, Medium Effort

### TD-09: Lazy-load the Whisper model

**Where:** `app.py:24-26`.

Move warmup off the boot path; let `run_transcription` pull on first request. See `performance-review.md#perf-02`. Fixes the slow HF Space health-check experience.

### TD-10: TranscriptionCache lifecycle

**Where:** `src/database/models.py:39-45`.

Add a TTL or a row cap. See `performance-review.md#perf-01`.

### TD-11: Strengthen prompt-injection detection

**Where:** `src/security/injection_detector.py:6-29`.

Normalize transcripts before matching, add a length cap, and document the protection as best-effort rather than complete. See `security-review.md#sec-03`.

### TD-12: Replace heuristic diarizer

**Where:** `src/agents/transcription.py:64-102`.

The current heuristic is brittle. A real diarizer (`pyannote-audio` or similar) is a substantial accuracy upgrade. Cost: a few hundred MB of model weights and a Hugging Face token. Only worth doing if speaker accuracy is a documented requirement.

## Lower Value Items

### TD-13: Centralize Pydantic v2 model defaults

`src/graph/state.py:76, 97` set `call_id: uuid.UUID = Field(default_factory=uuid.uuid4)` even though every caller provides the call_id from intake. The default factory is dead; removing it makes the contract clearer.

### TD-14: Drop `# ruff: noqa: E402` from `app.py` and `src/graph/workflow.py`

Both files import after a `logging.basicConfig`. The `noqa` is necessary because the call order matters, but a small comment explaining why would help future maintainers. Or, if you want the noqa to go away entirely, hoist the `logging.basicConfig` call into a tiny `src/_logging.py` module that gets imported first.

### TD-15: Type-narrow `db_engine: Any` in workflow nodes

`src/graph/workflow.py:52, 195, 238` accept `db_engine=None` but typed implicitly as `Any`. Adding `from sqlalchemy.engine import Engine` and annotating `db_engine: Engine | None` matches the strict mypy profile already declared in `pyproject.toml:46-49`.

### TD-16: Surface temp file count in observability

`_temp_files` in `src/services/pipeline.py:19` is invisible to operators. A counter exposed on the Observability tab would catch slow leaks before they fill `/tmp`.

## Architectural Observations (Not Debt, But Worth Noting)

- The graph in `src/graph/workflow.py` is currently linear once intake passes. There is no parallelism across stages. If accuracy gains from a second pass become important (for example, a second LLM that critiques the first's output), the LangGraph machinery is ready for it.
- The current Gradio UI is a single user, single tenant tool. Multi-user features (history scoping by `user_id`, RBAC) would require touching `src/database/models.py` and adding auth at the UI layer. Not implied by the current README.
- Audio storage is ephemeral (temp files). For audit replay and dispute resolution, you may want to persist the raw audio (with retention policy) under `data/audio/`. The `.gitignore` already excludes that directory.

None of these gaps make the current system unsafe or wrong. They are the natural growth trajectory of a healthy project.
