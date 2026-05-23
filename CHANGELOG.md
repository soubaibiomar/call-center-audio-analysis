# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `LICENSE` file matching the CC BY-NC 4.0 declaration in the README.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and this `CHANGELOG.md`.
- `docs/architecture.md` with system, sequence, state-machine, class, and ER diagrams, and a "what lives where" table mapping concepts to file paths and line ranges.
- `docs/getting-started.md` covering the minimal setup-to-first-call path.
- `docs/README.proposed.md` proposing further README enhancements without modifying the existing top-level `README.md`.
- `improvements/` folder containing an advisory audit: `IMPROVEMENT_PLAN.md` plus per-area reviews (code, security, performance, dependencies, testing, tech debt, accessibility) and applied-on-demand patches under `improvements/patches/`.
- `.editorconfig` describing whitespace conventions consistent with the existing code.
- `.github/workflows/ci.yml` running ruff (lint and format check) and pytest (unit and security suites) on every push and pull request.
- `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, and `.github/PULL_REQUEST_TEMPLATE.md`.
- `Dockerfile` mirroring the HuggingFace Space configuration for local container builds.

### Notes

- This release is documentation-only. No existing source file, test, or configuration was modified.
- The proposed code fixes for the audit findings live under `improvements/patches/` as standard `.patch` files. Apply with `git apply` at your discretion.

## [0.2.0] - prior release on `main`

Reference: the README at `README.md:1-499` describes the current functionality of version 0.2.0 in detail.
