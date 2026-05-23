# Code Review

Advisory review of correctness, readability, and idiomatic Python issues. Every finding cites the file and line range it refers to. Severity and effort tags follow the conventions in `IMPROVEMENT_PLAN.md`.

The overall code quality is good. Module boundaries are clean. Pydantic models are used consistently between pipeline stages. Type hints are present throughout. Most findings below are low-severity improvements rather than defects.

## CR-01: Silent bare-except in transcription cache

- **Severity:** Medium
- **Effort:** Small (under 30 minutes)
- **Files:** `src/agents/transcription.py:121-139, 142-164`

The cache read and cache write functions both catch every exception and return `None` or silently continue:

```python
# src/agents/transcription.py:138-139
    except Exception:
        return None
```

```python
# src/agents/transcription.py:163-164
    except Exception:
        pass  # Cache save failure is non-critical
```

The intent (cache must not break the pipeline) is correct. The implementation is a debugging hazard: if the SQLite engine is misconfigured, or `TranscriptionCache.transcription_json` deserialization fails because the schema drifted, neither failure is ever logged.

**Suggested fix.** Keep the same control flow but add `logger.exception(...)` inside the handler so the failure is recorded at WARNING or higher. Example:

```python
    except Exception:
        logger.exception("Transcription cache read failed")
        return None
```

A patch is provided under `improvements/patches/CR-01-log-cache-failures.patch`.

## CR-02: Module-level mutable globals

- **Severity:** Low
- **Effort:** Small (about one hour)
- **Files:** `src/services/pipeline.py:19-20`, `src/agents/transcription.py:18-19, 105-109`, `src/database/connection.py:42`

Three module-level mutable structures exist:

- `_temp_files: list[str]` in `src/services/pipeline.py:19` tracks generated temp files for rolling cleanup.
- `_model` and `_model_size` in `src/agents/transcription.py:18-19` cache the Whisper model singleton.
- `_session_factories: dict[int, sessionmaker]` in `src/database/connection.py:42` memoizes session factories per engine.

Each is correct for the single-process Gradio context, but they all carry the same costs: they make tests harder (the module must be reloaded between scenarios), they are not thread-safe under any backend other than Gradio's single-worker default, and they create hidden dependencies between modules.

**Suggested fix.** Move the state into a small dataclass or class that the existing factory functions (`compile_workflow`, `build_app`) own and pass through. Behavior stays identical. The fix is mostly mechanical and would not be a productive use of time unless there is a specific test or threading reason to do it.

If you keep the globals, consider adding a short comment at each declaration noting the single-process assumption so future contributors do not introduce concurrency that breaks it.

## CR-03: `DIMENSION_WEIGHTS` is never validated at startup

- **Severity:** Low
- **Effort:** Small (under 10 minutes)
- **Files:** `src/agents/qa_scoring.py:18-24, 129-135`

The QA dimension weights are declared as a literal dict that is expected to sum to `1.0`:

```python
# src/agents/qa_scoring.py:18-24
DIMENSION_WEIGHTS = {
    "professionalism": 0.15,
    "empathy": 0.20,
    "problem_resolution": 0.30,
    "compliance": 0.20,
    "communication_clarity": 0.15,
}
```

`_recompute_overall_score` at `src/agents/qa_scoring.py:129-135` multiplies each dimension score by its weight and sums. If a future edit changes a weight from `0.15` to `0.10` without adjusting another, the overall scores will silently drift below `5.0`, breaking the rubric documented in `README.md:206-213`.

**Suggested fix.** Add a single assertion next to the literal:

```python
assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9, (
    "DIMENSION_WEIGHTS must sum to 1.0"
)
```

This catches the drift at import time rather than after a deploy.

## CR-04: `config.py` always generates an unused encryption key

- **Severity:** Low
- **Effort:** Small (under 15 minutes)
- **Files:** `src/utils/config.py:14`

```python
# src/utils/config.py:12-14
# Auto-generate a DB encryption key if not provided.
# Persists for the lifetime of the process.
_DEFAULT_DB_KEY = secrets.token_hex(16)
```

The default key is generated at module import. It is then placed in `Config.db_encryption_key` if no `DB_ENCRYPTION_KEY` env var is set. However, the SQLCipher activation in `src/database/connection.py:23` requires the env var to be present:

```python
if encryption_key and os.environ.get("DB_ENCRYPTION_KEY"):
    ...
```

That means the auto-generated key is **never used** in practice. The default branch leaves the database unencrypted, which is what the README documents. The auto-generated key is dead code that suggests stronger behavior than the system actually provides.

**Suggested fix.** Remove `_DEFAULT_DB_KEY` and default `db_encryption_key` to `""` or `None`. The behavior is unchanged, and the misleading appearance of "we always have a key" goes away.

## CR-05: Lambdas inside the `StateGraph` constructor obscure tracing

- **Severity:** Low
- **Effort:** Small (about 20 minutes)
- **Files:** `src/graph/workflow.py:195, 198, 207-228`

The workflow assembly uses lambdas to bind extra arguments into the LangGraph nodes:

```python
# src/graph/workflow.py:195
workflow.add_node("transcribe_step", lambda s: transcription_node(s, config, db_engine))
```

This works, but LangSmith traces and exception messages refer to the node by its bound name only, with the wrapping lambda obscuring the underlying function name in some debuggers.

**Suggested fix.** Replace each lambda with `functools.partial`:

```python
from functools import partial
workflow.add_node(
    "transcribe_step",
    partial(transcription_node, config=config, db_engine=db_engine),
)
```

`functools.partial` preserves the wrapped function's `__name__` and is friendlier to debuggers. Behavior is identical.

## CR-06: Heuristic speaker diarization is brittle but undocumented as such

- **Severity:** Low
- **Effort:** Medium (rewrite is large, doc-only fix is small)
- **Files:** `src/agents/transcription.py:64-102`

The `SpeakerDiarizer` class uses a small set of regex patterns to decide whether each segment came from the agent or the customer. The heuristics are reasonable for the sample dataset under `data/samples/`, but they will misclassify in three predictable cases:

1. Calls where the customer opens the conversation (no agent greeting in segment 0).
2. Calls where the agent says something matching a "customer" pattern (for example, paraphrasing the customer's complaint back to them).
3. Calls with three or more participants (warm transfers, supervisor escalation).

There is no automatic fallback or confidence flag for these cases. Compared to a learned diarizer (such as `pyannote-audio`), accuracy is meaningfully lower.

**Suggested fix (low effort).** Add a comment to `SpeakerDiarizer` and to `docs/architecture.md` explaining the known weaknesses, so a reader does not assume a real diarization model is in place.

**Suggested fix (higher effort).** Integrate `pyannote-audio` behind a feature flag. Cost: about 500 MB of model weights, plus a Hugging Face token. Worth doing only if speaker accuracy is a documented requirement.

## CR-07: `compile_report` is called twice on the supervisor path

- **Severity:** Low
- **Effort:** Small (about 10 minutes)
- **Files:** `src/graph/workflow.py:149-187`

Both `report_node` and `supervisor_review_node` call `compile_report` independently. They compute the same `CallReport` with identical inputs except for the `status` field. This is fine, but it is duplicate logic: any future change to `compile_report` requirements (for example, adding a `model_used` field) has to be made in two places.

**Suggested fix.** Inline a `_make_report(state, status)` helper at the top of the file that both nodes call. The two nodes become two lines each. Behavior is unchanged.

## CR-08: PII metadata scan in intake is asymmetric with the redactor

- **Severity:** Low
- **Effort:** Small (about 20 minutes)
- **Files:** `src/agents/intake.py:19-24` versus `src/security/pii_redactor.py:22-31`

`intake._scan_metadata_for_pii` uses a different (looser) SSN pattern than `pii_redactor.redact_pii`:

- Intake: `\b\d{3}-\d{2}-\d{4}\b` (only dash separator).
- Redactor: `\b\d{3}[-\s]\d{2}[-\s]\d{4}\b` (dash OR whitespace).

The phone patterns also differ. The two should agree, or one should call the other.

**Suggested fix.** Have `intake._scan_metadata_for_pii` call `pii_redactor.redact_pii` and report `redaction_result.detections` rather than re-implementing patterns. One source of truth, fewer drift bugs.

## CR-09: `error_node` catches the wrong attribute when intake is `None`

- **Severity:** Low (no observed bug, only future-proofing)
- **Effort:** Small (about 5 minutes)
- **Files:** `src/graph/workflow.py:160-176`

The recovery code reads `state.get("intake")` and then `getattr(intake, "validation_error", None)`. This handles the case where intake is missing or has no error. However, it does not handle the case where the entire `state` is missing keys after a malformed user input. In practice the workflow always populates intake first, so this is theoretical. A defensive `if intake is not None and isinstance(intake, IntakeResult)` would be safer.

## CR-10: Patch suggestion file naming for owner review

If you would like to apply the suggested fixes one by one, the following patches are provided under `improvements/patches/`:

- `CR-01-log-cache-failures.patch` - adds `logger.exception` to the two cache handlers.
- `CR-03-assert-dimension-weights.patch` - one-line assertion that weights sum to 1.0.
- `CR-04-remove-unused-default-db-key.patch` - removes the dead `_DEFAULT_DB_KEY`.
- `SEC-01-parameterize-pragma-key.patch` - covered in `security-review.md`.

Apply with `git apply improvements/patches/<file>.patch`. None of these patches has been applied; the production code is unchanged.

## Already Good

Several things are worth calling out explicitly so future contributors do not "fix" them:

- The Pydantic models in `src/graph/state.py:1-116` are well-structured and use `Field(exclude=True, repr=False)` correctly to keep audio bytes out of logs.
- The `context_session` helper at `src/database/connection.py:52-63` is a textbook implementation of the unit-of-work pattern.
- `transcription._clean_transcript_text` at `src/agents/transcription.py:177-197` is a thoughtful piece of work. The repeat-phrase collapse loop in particular handles a real Whisper failure mode that many comparable projects ignore.
- The README's pipeline diagram (`README.md:98-114`) is accurate. It corresponds one-for-one with the nodes in `src/graph/workflow.py:190-235`.
