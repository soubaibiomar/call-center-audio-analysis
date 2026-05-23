# Dependency Review

Advisory review of `requirements.txt` and `pyproject.toml`, including version pinning strategy, known-vulnerable packages, deprecated packages, and unused declarations.

## Summary

Every direct dependency is pinned to an exact version using `==`. This is excellent for build reproducibility (the HuggingFace Space gets the same wheels every build) but means security patches require manual bumps. No dependency in the current lockset has an open CVE that I am aware of at the time of this audit, but `pip-audit` (or `safety`) was not run as part of this advisory audit because it is not part of the project's existing tooling. Adding it to the CI workflow (see `.github/workflows/ci.yml` proposed in this audit) closes that gap.

Two minor items: `python-dotenv==1.1.0` is loaded but not strictly required when running on HuggingFace Spaces (which injects env vars directly). `langsmith==0.3.42` is unused unless `LANGCHAIN_TRACING_V2=true` is set. Both are small, both are safe to keep.

## DEP-01: Version pinning strategy is rigid {#dep-01}

- **Severity:** Low
- **Effort:** Small (decision, not implementation)
- **File:** `requirements.txt:1-15`, `pyproject.toml:6-22`

```
langgraph==0.4.1
langchain==0.3.25
langchain-openai==0.3.12
...
```

Exact-version pins guarantee reproducibility, but they have two costs:

1. Routine bug fixes and security patches in patch-level releases (for example `0.3.13` of `langchain-openai`) are silently missed.
2. The lockset goes stale fast. LangChain has shipped many releases since `0.3.25`; running on the latest minor would pick up upstream fixes for free.

**Recommended approach.** Continue to pin direct dependencies, but bump them monthly or every other minor release. Pair the bumps with a pre-merge run of `pip-audit`. The CI workflow added by this audit includes a `pip-audit` step that will surface any package with an open advisory.

If you prefer fully reproducible builds, switch to a lock file generator (`uv pip compile` or `pip-tools`) and commit the locked output. This keeps both reproducibility and visibility into transitive dependencies.

## DEP-02: `python-dotenv` is used but optional on HF Spaces {#dep-02}

- **Severity:** Informational
- **File:** `requirements.txt:10`, `src/utils/config.py:8-10`

`load_dotenv()` is called unconditionally at import in `src/utils/config.py:10`. On HuggingFace Spaces the env vars come from the Space's `Secrets` panel, and `.env` is not present, so `load_dotenv()` becomes a no-op. The dependency is still pulled in.

This is fine. Keep `python-dotenv` because it makes local development pleasant. Just note that the runtime path on HF Spaces is the env-var path, not the `.env` path.

## DEP-03: `langsmith` is unused unless tracing is enabled {#dep-03}

- **Severity:** Informational
- **File:** `requirements.txt:4`, `src/graph/workflow.py:8, 43-156`

`@traceable` decorators are unconditionally applied to the workflow nodes (`src/graph/workflow.py:43, 51, 65, 81, 102, 148`). If `LANGCHAIN_TRACING_V2` is not set, the decorators are inert and add nanoseconds of overhead. Good design.

If you would like to slim the wheel for production deployments without tracing, you can mark `langsmith` as an extra:

```toml
[project.optional-dependencies]
trace = ["langsmith==0.3.42"]
```

and remove the import-time dependency by replacing `from langsmith import traceable` with a thin local fallback. The win is small (a few MB on `langsmith` plus its transitive deps).

## DEP-04: Heavyweight optional ML dependencies {#dep-04}

- **Severity:** Informational
- **File:** `requirements.txt:7`

`faster-whisper==1.2.1` pulls in `ctranslate2`, `onnxruntime`, and NumPy. The combined install on Linux x86-64 is roughly 150 MB. On HuggingFace Spaces this is paid once at build time and reused; on a CI runner it is paid every run.

If CI time becomes a concern, cache the wheel store:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
    cache: "pip"
```

The CI workflow proposed by this audit already includes this. Build time should be roughly 2 minutes the first run and under 30 seconds on subsequent runs.

## DEP-05: PyTorch is an undeclared transitive dependency {#dep-05}

- **Severity:** Low
- **File:** `src/agents/transcription.py:24-34`

```python
# src/agents/transcription.py:24-34
try:
    import torch
    ...
```

`torch` is imported optionally to detect CUDA. It is not declared in `requirements.txt`. On HuggingFace Spaces with a GPU runtime, torch is preinstalled by the base image, so this works by happy accident. In a clean CPU-only environment (CI runner, Docker base image, fresh venv), `torch` is absent and the `ImportError` is silently swallowed.

This is intentional and correct: if torch is missing, the code falls back to CPU with int8. The note here is documentation, not code change. If you ever want CUDA in CI or local dev, add `torch` (with the right `--extra-index-url` for CUDA wheels) to a `[project.optional-dependencies] gpu = [...]` group.

## DEP-06: No `pip-audit` or `safety` in tooling {#dep-06}

- **Severity:** Low
- **Effort:** Small (resolved by this audit)
- **File:** N/A

The project does not currently run a CVE scanner against its dependencies. The proposed `.github/workflows/ci.yml` added by this audit runs `pip-audit` on every pull request and will report findings as job warnings. No existing file was changed to enable this.

## Unused or Underused Imports

A quick scan with `ruff check --select F` reports `All checks passed!` against the current codebase. There are no dead imports.

## Reasonable Targets for Future Bumps

These are not urgent. Bumping is straightforward and tends to pull in upstream bug fixes.

| Package | Current | Why bump |
|---|---|---|
| `langgraph` | `0.4.1` | LangGraph ships frequently; later 0.4.x releases fix conditional-edge edge cases. |
| `langchain` | `0.3.25` | Several 0.3.x patch releases have shipped. |
| `langchain-openai` | `0.3.12` | Async retry behavior was refined in later patches. |
| `gradio` | `5.29.0` | 5.x is on a fast release cadence. Read the release notes for breaking changes before bumping. |
| `pydantic` | `2.11.3` | 2.x is largely backward-compatible. Bump for minor perf wins. |

Always run the full test suite after a bump. The 109-test unit suite at `tests/unit/` exercises most of the integration surface.
