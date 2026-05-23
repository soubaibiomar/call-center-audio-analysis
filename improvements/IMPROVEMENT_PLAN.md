# Improvement Plan

This document is the executive summary of an advisory audit of the Call Center Intelligence System. It is intended as the **first file an owner reads** when reviewing the `improvements/` folder. Every finding it references is backed by file and line citations in the detailed reports linked at the bottom.

No production code, configuration, or test was modified during this audit. Every change proposed below is either a brand-new file under `improvements/`, `docs/`, or `.github/`, or a finding that the owner can apply at their own discretion.

## Executive Summary

The Call Center Intelligence System is a well-engineered Python project. The codebase shows a clear separation of concerns across UI, services, agents, graph orchestration, and persistence layers; uses Pydantic v2 typed contracts between pipeline stages; and ships with 109 unit-level and security tests that pass cleanly on a fresh checkout. The existing README is unusually thorough for a personal project: it documents architecture diagrams, the QA rubric, environment variables, and per-hardware performance characteristics in detail.

The audit identifies **one high-severity issue** (a missing `LICENSE` file despite a publicly declared `CC BY-NC 4.0` license in the README), **three medium-severity issues** (an unsafe f-string in a SQLite PRAGMA, a PII regex that misses unseparated SSNs, and silent broad `except` blocks in the transcription cache), and a handful of low-severity quality, performance, and tech-debt items. None of these block release. Most are 30-minute fixes.

The most valuable additions delivered by this audit are **structural rather than corrective**: a `LICENSE` file matching the README's declared license, a `SECURITY.md` for private disclosure, `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` for community norms, a `Dockerfile` and CI workflow to make the build reproducible outside HuggingFace Spaces, and a deeper `docs/architecture.md` that maps every concept in the README back to specific file paths and line ranges.

## Overall Health

| Dimension | Rating | Evidence |
|---|---|---|
| Architecture | Strong | Five clean layers; thin 36-line `app.py:1-36` entrypoint; typed Pydantic contracts in `src/graph/state.py:1-116`. |
| Tests | Strong | 109 unit and security tests pass; 4 integration tests need LLM keys. |
| Documentation | Strong | Existing `README.md` is 23 KB and includes 5 mermaid diagrams. |
| Security posture | Moderate | Layered defenses are in place (`src/security/injection_detector.py`, `src/security/pii_redactor.py`), but the regex patterns are bypassable and one PRAGMA call is unsafely constructed. |
| Dependency hygiene | Moderate | All dependencies pinned to exact versions, which is good for reproducibility but means patches require manual bumps. |
| Repo health | Weak | No `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, `Dockerfile`, or CI workflow exist on `main` at the time of audit. |
| Performance | Strong | Cold-start optimizations are explicit and documented; the SHA-256 transcription cache, int8 quantization, and `beam_size=1` are well-justified trade-offs. |

## Top Findings (cross-report, sorted by severity)

| ID | Severity | Effort | Area | Where | Summary |
|---|---|---|---|---|---|
| LIC-01 | High | Small | Licensing | `README.md:499` declares `CC BY-NC 4.0`; no `LICENSE` file exists | Add a matching `LICENSE` file to make the declaration enforceable. Resolved by this audit. |
| SEC-01 | Medium | Small | Security | `src/database/connection.py:29` | `cursor.execute(f"PRAGMA key='{encryption_key}'")` constructs the SQL via f-string. A key containing `'` would break the statement. See `security-review.md#sec-01`. |
| SEC-02 | Medium | Small | Security | `src/security/pii_redactor.py:23` | SSN pattern requires a `-` or whitespace separator. An unbroken nine-digit string like `123456789` is not redacted. See `security-review.md#sec-02`. |
| SEC-03 | Medium | Small | Security | `src/security/injection_detector.py:6-29` | Patterns are simple, case-insensitive regex. Easy to bypass with character substitution or zero-width insertions. See `security-review.md#sec-03`. |
| CR-01 | Medium | Small | Code review | `src/agents/transcription.py:138-139, 163-164` | Bare `except Exception` blocks swallow cache failures silently. Add a `logger.exception` so debugging is possible without flipping a flag. See `code-review.md#cr-01`. |
| PERF-01 | Medium | Medium | Performance | `src/database/models.py:39-45` | `TranscriptionCache` grows without bound. Add a TTL column and a cleanup job, or cap the table size. See `performance-review.md#perf-01`. |
| CR-02 | Low | Small | Code review | `src/services/pipeline.py:19, src/agents/transcription.py:18-19, src/database/connection.py:42` | Module-level mutable globals make testing harder and add hidden coupling. See `code-review.md#cr-02`. |
| CR-03 | Low | Small | Code review | `src/agents/qa_scoring.py:18-24, 129-135` | `DIMENSION_WEIGHTS` is defined once but never asserted to sum to 1.0. See `code-review.md#cr-03`. |
| PERF-02 | Low | Small | Performance | `app.py:24-26` | Whisper model is loaded synchronously in the entrypoint, blocking Gradio launch until the model is ready. See `performance-review.md#perf-02`. |
| DEP-01 | Low | Small | Dependencies | `requirements.txt:1-15` | Versions are pinned with `==` and not constrained to a range. Security patches require manual bumps. See `dependencies.md#dep-01`. |

The full lists, including low-severity items not promoted here, live in the per-report documents below.

## Prioritized Roadmap

### Quick wins (under one hour, high value)

1. Add the `LICENSE` file matching the README declaration. **Already created by this audit at the repo root.**
2. Fix `SEC-01` by switching the PRAGMA call to a parameterized statement or by escaping the key.
3. Fix `SEC-02` by adding an unseparated-SSN pattern alongside the existing one.
4. Fix `CR-01` by changing `except Exception:` to `except Exception:` with `logger.exception(...)`.
5. Add an assertion that `DIMENSION_WEIGHTS.values()` sums to `1.0` at import time (`CR-03`).

### Medium term (one to four hours each)

6. Add a `created_at`-based eviction job or a hard row cap to `TranscriptionCache` (`PERF-01`).
7. Strengthen `injection_detector.py` by lowercasing AND normalizing whitespace before matching, and adding a length cap so very long transcripts cannot starve the regex engine (`SEC-03`).
8. Move Whisper model loading out of the import-time path. Lazy-load on first transcription request and add a warmup endpoint so HF Spaces' health check still passes (`PERF-02`).
9. Replace the module-level globals in `pipeline.py` and `transcription.py` with a small class that the workflow factory owns (`CR-02`). Keeps behavior identical, removes test friction.

### Larger efforts (over half a day)

10. Replace the heuristic speaker diarizer in `src/agents/transcription.py:64-102` with `pyannote-audio` or a learned model for substantial accuracy gains. Cost: a few hundred MB of model and ~10 seconds of additional cold-start time.
11. Add LLM-mocked integration tests so the four tests under `tests/integration/test_pipeline_end_to_end.py` can run in CI without API keys.
12. Consider migrating from raw regex PII redaction to a maintained library such as Microsoft Presidio. Trade-off: heavier dependency, but far more comprehensive coverage.

## Decisions That Need the Owner

- **License confirmation.** The README declares `CC BY-NC 4.0` at `README.md:499`. This audit added a matching `LICENSE` file at the repo root. If the intended license is something else (for example, MIT or Apache-2.0), replace the `LICENSE` file content and update the README badge accordingly.
- **CI scope.** The proposed CI workflow at `.github/workflows/ci.yml` runs ruff, pytest unit and security tests, and the security audit. It does **not** run integration tests (which need API keys). If you want the integration tests to run on PRs, configure `OPENAI_API_KEY` as a repository secret and remove the `-m "not integration"` filter.
- **Production deployment target.** The README mentions HuggingFace Spaces as the live demo target. The added `Dockerfile` mirrors that configuration but is independent of HF Spaces, so the same image can be run on Fly.io, Render, or any container host. Pick the path that fits your operating model.

## Detailed Reports

- [code-review.md](code-review.md) - correctness, readability, and idiomatic issues.
- [security-review.md](security-review.md) - injection, PII, secret handling, transport, and dependency security.
- [performance-review.md](performance-review.md) - hot paths, blocking calls, cache lifecycle, and database growth.
- [dependencies.md](dependencies.md) - dependency hygiene, version pinning strategy, unused packages.
- [testing-gaps.md](testing-gaps.md) - what is covered, what is not, and the highest-value tests to add.
- [tech-debt-and-refactoring.md](tech-debt-and-refactoring.md) - structural improvements, prioritized by value over effort.
- [accessibility-and-ux.md](accessibility-and-ux.md) - Gradio UI usability and accessibility notes.

## Acknowledgments

This audit was completed without modifying any existing file in the repository. The owner remains the sole author of every line of production code, configuration, and test.
