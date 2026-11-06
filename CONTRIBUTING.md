# Contributing

Contributions preserve the original Call Center Intelligence behavior while Project 28
adds Adaptive Call Center Intelligence capabilities. Follow the detailed
[Project 28 development workflow](docs/development/workflow.md) for ownership,
review, branch/commit conventions, conflicts, evidence and merge requirements.
The workflow defines local policy; remote protections and labels are not activated
merely by adding these files.

## Local Setup

### Native Windows development

Use PowerShell and a uv-managed Python 3.12 environment; do not use Conda. The
authorized dependency/setup step owns environment changes. When establishing a
new development environment deliberately, the project commands are:

```powershell
uv venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -e ".[dev]"
```

Inspect an existing environment before changing it. Never overwrite an existing
`.env`; configure credentials privately using the setup documentation. FFmpeg is
required for native audio operations; its host PATH absence is recorded in STEP_01.
The existing Docker baseline offers a documented alternative. Hook configuration
is in `.pre-commit-config.yaml`; installation/platform validation is a separate
deliberate setup action, not something these instructions silently perform.

### Docker

If you do not want to install Python dependencies on your host:

```bash
docker build -t call-center-intel .
docker run -p 7860:7860 --env-file .env call-center-intel
```

The container runs the same Gradio app as `make run` and listens on port 7860.

## Running Tests Locally

From the existing uv-managed Windows environment:

```powershell
.venv/Scripts/python.exe -m pytest tests/ -q --tb=short
.venv/Scripts/python.exe -m ruff check src/ tests/ app.py
.venv/Scripts/python.exe -m ruff format --check src/ tests/ app.py
.venv/Scripts/python.exe -m mypy src/
git diff --check
```

Run focused checks for any changed development scripts as well. These commands
do not install dependencies or launch models. Report actual exit codes and
failures: full-project typing currently fails as documented in STEP_01/STEP_02;
do not describe it as passed merely because a scoped check passes. The Makefile
remains available for compatible shells. Current integration tests use mocked
model/provider boundaries; their passing does not prove live model quality.

## Branch and PR Conventions

Use a scoped branch and preserve existing uncommitted work. The already-existing
`feature/project28-foundation` branch is reused; future names, responsibility
boundaries and conflict procedures are in workflow rules W01–W06. Complete the
[PR template](.github/PULL_REQUEST_TEMPLATE.md), including tests, security,
documentation and measured ML/UI evidence where applicable. The other developer
must approve the current revision before an authorized merge. Names/teams must be
real; local reports do not substitute for independent human approval.

## Commit Message Style

Use Conventional Commits at cohesive, validated milestones:

```text
<type>(<optional scope>): <concrete outcome>

Why the change was needed, its scope and material validation.
```

Group related implementation, configuration, documentation and tests. Avoid tiny
per-edit commits or minute-based scheduling. Commit and push only when authorized.
Adjusted dates spanning days require explicit intended dates and timezone from
the user; do not invent a schedule or imply elapsed engineering time. Published
history rewrites and force pushes require separate authorization. See W07–W08.

## Style Guide

- **Formatter:** `ruff format`. Run `make format` to apply.
- **Linter:** `ruff check` with the rules in `pyproject.toml:38-43`. Run `make lint` to verify.
- **Type checker:** `mypy --strict` on `src/`. Run `make typecheck`.
- **Pre-commit configuration** at `.pre-commit-config.yaml` defines formatter/linter/secret checks. Installed hook behavior must be validated on the target platform; STEP_03 does not install or certify hooks. Do not bypass active checks with `--no-verify`.
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
- Actual behavior (sanitized error message and stack trace if available).
- Your environment: Python version (`python --version`), OS, whether you are running native or Docker.
- A minimal reproduction. For audio-related bugs, prefer a synthetic reproduction; share recordings only with verified permission and appropriate privacy handling.

For **security-relevant** bugs, do not file a public issue. See `SECURITY.md` for the private disclosure path.

## Code Review Expectations

PRs are reviewed for:

1. Correctness against the existing test suite.
2. Consistency with the patterns already in the codebase.
3. Whether the change earns its complexity. A 200-line PR that fixes a one-line bug needs a paragraph in the description explaining why.
4. Test coverage for new code paths.

Reviewers may ask for changes; this is normal. If a request is unclear, ask. The goal is to ship the right code, not to ship the original code.

## License of Contributions

By submitting a pull request, you agree that your contribution is licensed under the same MIT terms as the project (see `LICENSE`). Do not contribute code you do not have the right to license.
