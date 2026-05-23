# Contributing

Thanks for your interest in improving the Call Center Intelligence System. This document covers how to set up the project locally, the branch and PR conventions, the style guide, what is in scope and out of scope, and how to report bugs.

## Local Setup

### Native (recommended for development)

```bash
git clone https://github.com/ANI-IN/Call-Center-Intelligence-System.git
cd Call-Center-Intelligence-System

python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

pip install -e ".[dev]"
pre-commit install

cp .env.example .env
# edit .env to add at least one LLM API key
```

You also need `ffmpeg` available on `PATH`. On macOS: `brew install ffmpeg`. On Debian / Ubuntu: `apt install ffmpeg`. On Windows: `choco install ffmpeg`.

### Docker

If you do not want to install Python dependencies on your host:

```bash
docker build -t call-center-intel .
docker run -p 7860:7860 --env-file .env call-center-intel
```

The container runs the same Gradio app as `make run` and listens on port 7860.

## Running Tests Locally

```bash
make test               # unit + security suites (no API calls, under 20s)
make test-integration   # full pipeline (requires an LLM key in .env)
make test-security      # security suites only
make test-all           # everything
```

Run `make test` before opening a PR. It is the same gate CI enforces on every push.

## Branch and PR Conventions

- Create a branch from `main` named `<type>/<short-description>`. Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`, `perf`.
- Examples: `feat/strict-injection-normalization`, `fix/cache-error-logging`, `docs/architecture-rewrite`.
- Keep PRs small. A PR that fixes one bug and refactors three modules is harder to review than two separate PRs.
- Open the PR as a draft if you want early feedback. Mark it ready for review once CI is green.
- Squash on merge is preferred. The PR title becomes the squashed commit message.

## Commit Message Style

This repository uses **Conventional Commits**:

```
<type>(<optional scope>): <short summary in imperative mood>

<optional body explaining the why>

<optional footer with breaking changes or issue refs>
```

Examples:

- `feat(qa): assert dimension weights sum to 1.0 at import`
- `fix(transcription): log cache failures instead of swallowing`
- `docs: add architecture diagram for the LangGraph state machine`
- `chore: add CI workflow with ruff and pytest`

## Style Guide

- **Formatter:** `ruff format`. Run `make format` to apply.
- **Linter:** `ruff check` with the rules in `pyproject.toml:38-43`. Run `make lint` to verify.
- **Type checker:** `mypy --strict` on `src/`. Run `make typecheck`.
- **Pre-commit hooks** at `.pre-commit-config.yaml` enforce the formatter, the linter, and `detect-secrets` on every commit. Do not bypass with `--no-verify`.
- **Line length:** 100 characters (`pyproject.toml:40`).
- **Imports:** Sorted by ruff's `I` rule. Avoid relative imports beyond a single dot.
- **Docstrings:** One-line summary on every public function; longer docstrings only when the behavior is non-obvious. Existing modules show the style.
- **Comments:** Default to none. Add one only when the *why* is non-obvious. Never paraphrase what the code already says.

## What Is In Scope

- Bug fixes against the documented behavior.
- New tests that improve coverage of the riskiest untested paths.
- Documentation improvements that stay accurate to the code.
- Performance refinements with a measured before / after.
- Security hardening, especially around the prompt-injection and PII redaction layers.
- New LLM providers that conform to the `BaseChatModel` interface used by `src/utils/llm_factory.py`.

## What Is Out of Scope

- Architectural rewrites without prior discussion in an issue.
- Adding heavy dependencies (Pyannote, Presidio, Triton, etc.) without an issue describing the value and the trade-offs.
- Cosmetic reformatting of unmodified files.
- Renaming or moving public modules without a deprecation window.
- Test changes that depend on real LLM calls in CI.

## Bug Reports

Open an issue on GitHub with:

- The exact command or UI action that triggered the bug.
- Expected behavior.
- Actual behavior (full error message and stack trace if available).
- Your environment: Python version (`python --version`), OS, whether you are running native or Docker.
- A minimal reproduction. For audio-related bugs, attach a small sample audio if you can share one.

For **security-relevant** bugs, do not file a public issue. See `SECURITY.md` for the private disclosure path.

## Code Review Expectations

PRs are reviewed for:

1. Correctness against the existing test suite.
2. Consistency with the patterns already in the codebase.
3. Whether the change earns its complexity. A 200-line PR that fixes a one-line bug needs a paragraph in the description explaining why.
4. Test coverage for new code paths.

Reviewers may ask for changes; this is normal. If a request is unclear, ask. The goal is to ship the right code, not to ship the original code.

## License of Contributions

By submitting a pull request, you agree that your contribution is licensed under the same terms as the project (CC BY-NC 4.0, see `LICENSE`). Do not contribute code you do not have the right to license.
