# Performance Review

Advisory review of hot paths, blocking calls, cache behavior, and database growth. Most performance concerns documented in the README are already addressed in code (greedy decoding, VAD filter, int8 quantization, SHA-256 transcription cache). The findings below are the remaining gaps.

## PERF-01: TranscriptionCache grows without bound {#perf-01}

- **Severity:** Medium
- **Effort:** Medium (one to two hours)
- **Files:** `src/database/models.py:39-45`, `src/agents/transcription.py:142-164`

The `TranscriptionCache` table records every transcription forever. Each row holds a SHA-256 hash plus the full `TranscriptionResult.model_dump_json()`. For typical 5- to 15-minute calls the JSON is roughly 5 to 20 KB. After 10,000 unique calls the table will be 50 to 200 MB. After 100,000, gigabytes.

There is no eviction policy. There is no TTL. There is no size cap. The only retrieval lookup is by `audio_hash`, so the table is essentially write-once: stale rows are kept forever even when their corresponding audio bytes will never be seen again.

**Recommended fix.** Add a cleanup pass that drops rows older than a configurable age (for example, 30 days) at app startup, or at the end of every successful pipeline run. The query is one line:

```python
session.query(TranscriptionCache).filter(
    TranscriptionCache.created_at < datetime.now() - timedelta(days=30)
).delete()
```

Alternatively, keep the most recent `N` entries by `created_at` and delete the rest. `N=1000` is a reasonable default for a single-host deployment.

## PERF-02: Whisper model loads synchronously at startup {#perf-02}

- **Severity:** Low (Medium on cold starts)
- **Effort:** Small (about 30 minutes)
- **Files:** `app.py:24-26`, `src/agents/transcription.py:37-48`

The entrypoint blocks until the Whisper model is loaded:

```python
# app.py:24-26
print(f"Loading Whisper model ({config.whisper_model_size})...")
_get_whisper_model(config.whisper_model_size)
print("Whisper model loaded.")
```

For `WHISPER_MODEL_SIZE=tiny` (the default) this takes 5 to 15 seconds. For `large-v3` it takes 30 to 90 seconds, plus the model weights download (~3 GB) on the first run. During this window, Gradio is not yet listening on port 7860, so a HuggingFace Space build report shows `Building...` for the entire load duration.

**Recommended fix.** Move the warmup out of the import-time path. The cleanest approach is to:

1. Remove the explicit `_get_whisper_model(...)` call from `app.py`.
2. Let `run_transcription` lazy-load on first invocation as it already does at `src/agents/transcription.py:37-48`.
3. Optionally add a `gr.Blocks.load(lambda: _get_whisper_model(...))` callback so the model warms after the UI is up.

The trade-off is that the very first user request takes longer. For HF Spaces this is a clear win: faster health checks, faster perceived boot.

## PERF-03: Sequential summary then QA, but transcript is re-serialized

- **Severity:** Low
- **Effort:** Small (under 30 minutes)
- **Files:** `src/graph/workflow.py:102-145`, `src/agents/summarization.py:46-52`, `src/agents/qa_scoring.py:114-126`

The combined node calls `_format_transcript` in summarization, then `_format_input` in QA scoring. Both walk all segments and emit a `[MM:SS-MM:SS] Speaker: text` line. For a 10-minute call with ~100 segments, both functions repeat the same string building work.

The cost is negligible (sub-millisecond), but the duplication is worth a small refactor:

**Suggested fix.** Pull the segment formatter into `src/utils/formatters.py` and call it from both `summarization.py` and `qa_scoring.py`. A new function `format_transcript_segments(segments)` keeps each agent file shorter and removes the drift risk.

## PERF-04: Audit log read on every Observability tab open

- **Severity:** Low
- **Effort:** Small
- **Files:** `src/services/observability.py:12-105`

Each time the user clicks the Observability tab, the dashboard recomputes from scratch: it counts every row in `CallRecord` and `AuditLogEntry`, then deserializes every QA scores JSON to compute the average score. The deserialization at `src/services/observability.py:37-48` runs once per completed call.

For a few hundred calls this is fine (under 100 ms). For 100,000+ calls, the dashboard load becomes visible.

**Recommended fix.** Either:

- Maintain a small `metrics` table (`total_calls`, `total_completed`, `sum_overall_score`, `count_overall_score`) updated transactionally inside `persist_report`, so the dashboard becomes a single-row SELECT, or
- Cache the dashboard result in memory with a 5-second TTL.

This is premature for the current scale but worth noting in the file.

## PERF-05: `list_calls` does no pagination, only a hard limit

- **Severity:** Low
- **Effort:** Small (under one hour)
- **Files:** `src/services/history.py:32-68`

The History tab loads up to 200 rows at a time (`src/services/history.py:32`). Older calls remain accessible by raising the limit (or are silently dropped from the UI). The Gradio `Dataframe` can render 200 rows fast, but the UX once the table exceeds 200 entries is "older calls disappear", with the README at `data/samples/README.md` not explaining how to surface them.

**Recommended fix.** Add `offset` and `limit` parameters and surface a "Load more" button. Keep the default 200 but allow pagination.

## PERF-06: Per-segment PII redaction is O(segments * patterns)

- **Severity:** Low (current scale)
- **Effort:** Small
- **Files:** `src/graph/workflow.py:81-99`

The PII redaction node iterates every segment and runs all PII patterns against each:

```python
# src/graph/workflow.py:91-99
for seg in transcription.segments:
    seg_result = redact_pii(seg.text)
    redacted_segments.append(seg.model_copy(update={"text": seg_result.redacted_text}))
```

For a 100-segment call with 4 PII patterns this is 400 regex runs. Negligible. For a 30-minute call with 600 segments it is still under 100 ms. The note here is preventative: if PII patterns are extended to a larger set (Presidio has hundreds), batch them by joining segments with a separator, redacting once, then splitting.

## PERF-07: PDF generation pulls the full report into memory

- **Severity:** Low
- **Effort:** Small (not worth fixing today)
- **Files:** `src/agents/report.py:73-119`

`generate_report_pdf` uses ReportLab's `SimpleDocTemplate` to render the entire call report into an in-memory `BytesIO`. For a typical report this is tens of KB, fine. The only concern is that the PDF and the JSON download in `src/services/pipeline.py:155-163` both buffer to disk in `/tmp`, and on a long-running process these temp files accumulate until `_cleanup_old_temp_files` rotates them (`src/services/pipeline.py:23-33`).

The rotation cap is 50 files. On a busy server (1 call per minute), that means the `/tmp` directory will hold roughly 50 minutes of artifacts. If disk space is tight, lower the cap or eagerly delete the files after Gradio has served them.

## Strengths Worth Preserving

- **`beam_size=1`** at `src/agents/transcription.py:225`. Documented in the README as a deliberate ~2x speedup.
- **VAD filter** at `src/agents/transcription.py:227-228`. Skipping silent segments saves 20-30% of decode time.
- **`condition_on_previous_text=False`** at `src/agents/transcription.py:230`. Prevents the well-known Whisper hallucination loop.
- **int8 quantization on CPU** at `src/agents/transcription.py:31, 34`. 2-4x faster on CPU with minimal quality loss for clear English.
- **SHA-256 cache** at `src/agents/transcription.py:112-164`. Instant on repeat for identical audio, even across process restarts.
- **`sessionmaker` reuse** at `src/database/connection.py:42-49`. Avoids per-call session-factory construction.

The performance profile of this system is genuinely well-thought-out. The findings above are refinements, not corrections.
