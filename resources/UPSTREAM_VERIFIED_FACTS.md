# Upstream repo fact sheet — public README & pyproject snapshot (2026-10-24)

Source: https://github.com/ANI-IN/Call-Center-Intelligence-System

This is a public-source briefing, **not a local clone or independent test**. Verify against local pinned SHA in Step 02.

- `app.py` launches Gradio; `src/graph/workflow.py` builds LangGraph; `src/services/pipeline.py` connects graph and UI.
- faster-whisper speech-to-text; speaker assignment is a heuristic in `src/agents/transcription.py`, **not neural diarization**.
- Existing agents include summarization and QA weighted scoring (`src/agents/qa_scoring.py` weights: professionalism .15, empathy .20, resolution .30, compliance .20, clarity .15).
- PII redactor and injection detector under `src/security/`, cache keyed by SHA-256, SQLite (`CallRecord`, `AuditLogEntry`, `TranscriptionCache`), ReportLab PDF/JSON and LangSmith optional tracing.
- 3-tab Gradio UI (Analyze Call, History, Observability) and bundled sample MP3s.
- Original selectable LLM providers: OpenAI, Gemini, Groq. No native Ollama provider advertised.
- Original documented limitations: no true speaker diarization, multi-tenant authentication, or streaming transcription.
- pyproject requires Python >=3.11 and lists pinned dev dependencies pytest/ruff/mypy/pre-commit.
- All performance figures and test counts reported by the original maintainers require actual reproduction; do not repeat as your own benchmark.

See README and docs/architecture.md of the pinned clone for precise symbols and differences.
