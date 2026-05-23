# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `LICENSE` file (MIT) at the repo root.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and this `CHANGELOG.md`.
- `docs/architecture.md` with system, sequence, state-machine, class, and ER diagrams, and a "what lives where" table mapping concepts to file paths and line ranges.
- `docs/getting-started.md` covering the minimal setup-to-first-call path.
- `.editorconfig` describing whitespace conventions consistent with the existing code.
- `.github/workflows/ci.yml` running ruff (lint and format check) and pytest (unit and security suites) on every push and pull request.
- `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, and `.github/PULL_REQUEST_TEMPLATE.md`.
- `Dockerfile` mirroring the HuggingFace Space configuration for local container builds.

### Changed

- Rewrote the top-level `README.md` to the 24-section comprehensive structure with ASCII demo, knobs table, deeper troubleshooting, and project structure tree. HF Spaces YAML frontmatter preserved.
- Switched license from `CC BY-NC 4.0` to `MIT` for broader reuse.

### Notes

- No production source file (anything under `src/`, `tests/`, `app.py`, `pyproject.toml`, `requirements.txt`, `Makefile`, `.gitignore`, `.env.example`, `.pre-commit-config.yaml`) was modified.

## [0.2.0] - prior release on `main`

Reference: the README at `README.md:1-499` describes the current functionality of version 0.2.0 in detail.
