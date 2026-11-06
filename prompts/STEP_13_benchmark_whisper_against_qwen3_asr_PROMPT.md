# 13 — Benchmark Whisper against Qwen3-ASR | GPT-6.1 Sol (Medium)

## Approved UI reference
The approved product UI reference is `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`.
Whenever this step affects frontend behavior, screens, APIs that shape screens, or report screenshots, align the result with the Commercially-style design system in `design/UI_DESIGN_SYSTEM.md`.


**Project:** Adaptive Call Center Intelligence (Project 28)  
**Upstream:** https://github.com/ANI-IN/Call-Center-Intelligence-System  
**Schedule:** W1–W3 of 8 weeks  
**Lead:** ML  
**Required report:** `docs/implementation/STEP_13_benchmark_whisper_against_qwen3_asr_REPORT.md`

## Role and objective
You are the coding engineer responsible for **benchmark whisper against qwen3-asr**. Select an ASR baseline using task-specific evidence rather than model reputation.

Read `PROJECT28_MASTER_INSTRUCTIONS.md`, previous completed step reports, and actual repository code first. This prompt is a **self-contained instruction to execute one development step**, not to generate hypothetical code or a plan only.


## Approved Project 28 ERP visual direction — mandatory

**Read** `design/UI_DESIGN_SYSTEM.md`, `design/UI_ACCEPTANCE_CHECKLIST.md`, and visually inspect `design/APPROVED_GREEN_ERP_REFERENCE.png` before modifying any user-facing surface. The screenshot was approved by the user and supersedes all earlier blue/pink mockups. Use a **light sidebar, warm-white/light-neutral canvas, forest/emerald green interactions, dark readable typography, restrained rounded white cards, clean tables and truthful charts**. **No blue or pink** as primary, chart, link, focus, navigation or decorative colors. Use amber/red only for semantic warnings and errors; keep proper WCAG AA contrast and keyboard navigation.

For UI-related work, capture actual desktop/mobile screenshots and inspect against the reference; for non-UI work, document how actual API/data changes will support the approved UI, or mark visual impact `Not applicable`. Do not redesign the original Gradio baseline in early setup steps; retain it as a regression baseline until feature parity. **Reference image metrics are mock content and must never be copied as real results.**

**Step-specific visual/API contract:** Record WER, CER, latency, GPU memory and model IDs using schema suitable for model comparison charts; charts must not fake missing data.

**Documentation:** your matching Markdown report must contain `## 13. Approved ERP UI design / visual contract verification`, naming real files/routes, screenshot evidence if available, color/interaction/a11y checks, original Gradio vs new UI behavior, and any verified mismatch or unresolved work.

## Tasks to execute
1. Define uniform transcribe() interfaces and stable transcription JSON schemas.
2. Benchmark faster-whisper and Qwen3-ASR 0.6B on identical held-out authorized telephone audio.
3. Measure WER/CER, language/code-switching breakdown, p50/p95 latency, VRAM and failure rate.
4. Choose the deployment candidate with evidence and preserve a fallback adapter.

## Upstream code and proposed touch points
Inspect the actual repository files and distinguish upstream paths (existing) from proposed paths (may need creation). Do not assume a file exists just because it appears here.
- `src/agents/transcription.py`
- `ml/asr/`
- `ml/evaluation/asr_benchmark.py`
- `docs/benchmarks/ASR_BASELINE.md`

## Technologies and code/imports that must be explained
- **faster-whisper** — confirm relevant symbols/versions and explain every import introduced.
- **Qwen3-ASR** — confirm relevant symbols/versions and explain every import introduced.
- **jiwer** — confirm relevant symbols/versions and explain every import introduced.
- **CER/WER normalization** — confirm relevant symbols/versions and explain every import introduced.

## Required engineering implementation detail
- Document entry points, modules/functions/classes, typed schemas and inputs/outputs.
- For each import you **actually** add, explain e.g. `from X import Y`: what `X` is, what `Y` provides, why this project needs it, and runtime/training implications. If no imports are added, say so.
- Explain important code excerpts line-by-line, algorithms/transformations, errors/exception handling, why you placed code in its files, and example execution with real or synthetic non-sensitive fixtures.
- Include the full exact **existing vs upgraded implementation** matrix grounded in actual upstream HEAD and final working tree. Use `git diff --stat`, `git diff --name-status`, and specific code references.
- Add tests before or alongside implementation. Respect 8 GB VRAM and privacy/consent boundaries; do not claim a neural model learned unless gradient-based training actually ran.

## Required validation and done gate
- [ ] At least two model configs evaluated or blockers documented
- [ ] Reproducible benchmark manifest
- [ ] No hidden test-set tuning

## Analytics and evidence to include
- WER/CER language slices: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).
- real-time factor: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).
- GPU memory: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).

## Concepts and anticipated Q&A (expand with at least two more after implementation)
- **Q: Why benchmark both?**  
  **A: Arabic benchmarks do not prove Darija call-center performance.**
- **Q: What is WER?**  
  **A: Edit distance in word units divided by reference words.**
- **Q: Why report latency and VRAM?**  
  **A: A more accurate model may be unusable for live 8 GB GPU inference.**

## Mandatory documentation outcome
Create or update `docs/implementation/STEP_13_benchmark_whisper_against_qwen3_asr_REPORT.md` **after executing** the step. Start from the supplied `report_templates/STEP_13_benchmark_whisper_against_qwen3_asr_REPORT.md` template, but replace unexecuted placeholders with observed details. Record failures and blockers honestly. If implementation cannot be completed, write a truthful `PARTIAL`/`BLOCKED` report with exact next actions.

### Required sections in the final Markdown report (none may be omitted)
1. Header: step, owner, date, branch, upstream SHA, working SHA, status (DONE/PARTIAL/BLOCKED), environment.
2. Plain-English explanation: goal, problem solved, what was actually done, why, and what was not done.
3. Before/after matrix: **upstream actual implementation**, modified implementation, exact path/symbol, behavioral difference, backward compatibility.
4. Files inventory: created/modified/deleted files with purpose, interfaces, inputs/outputs and why each file exists.
5. Code explanation: meaningful changed code blocks and explanation **line by line or logical block**, algorithm, data flow, exceptions and edge cases; do not paste huge files.
6. Imports/dependencies: each newly introduced import/module, its origin (stdlib/third-party/local), reason, where used, version, and alternatives considered.
7. Concepts explained: definitions, mental model, tradeoffs and at least one concrete example that a beginner can follow.
8. Data, model and security: permissions, PII handling, data types/schemas, model/dataset versioning, failure modes, whether training happened.
9. Verification: exact commands, test pass/fail/skip, logs/evidence, API/UI proof and regression status.
10. Analytics/report: metric definitions, observed numeric values, sample size, hardware, baseline comparison and interpretation; mark unmeasured as `Not measured`.
11. Questions and **answered** responses: at least 5 step-specific engineering or conceptual Q&A, including one failure/tradeoff question.
12. Decision log, risk register, remaining work, dependencies and handoff for next step. End with an evidence checklist and links to repository artifacts.
13. Approved green-neutral ERP UI design: specific before/after behavior, token compliance, UI evidence and accessibility checks, or justified Not applicable.

## Global engineering and truthfulness rules

1. **Execute, do not only explain.** Inspect repository state before edits, then implement only the named step. If tooling is missing, report the exact blocker and non-destructive workaround; never invent commands, test results, file changes or benchmarks.
2. **Protect upstream compatibility.** Record `git rev-parse HEAD`, baseline branch, and the actual existing symbols/files before changing anything. Source locations listed in this prompt are candidates; confirm they exist at the pinned SHA. Preserve Gradio, LangGraph, faster-whisper, QA weighting, PII handling, caching, audit and PDF/JSON until replaced by tested alternatives.
3. **Work safely.** Do not delete data; overwrite work; modify unrelated services; push commits; deploy public services; buy resources; expose tokens; or download large datasets/models without explicit authorization. Use synthetic/consented fixtures only. Data allowed for analysis is not automatically permitted for model training.
4. **Hardware discipline.** Windows + PowerShell + VS Code + `uv` (not Conda), Docker Desktop, NVIDIA RTX 4060 8 GB, existing Ollama. Prefer CPU-first smoke checks and one GPU-heavy operation at a time; report measured peak VRAM.
5. **One step, one durable report.** After the attempt, replace the matching Markdown template under `docs/implementation/` with a **factual completed or blocked report** in English. Include code and imports explained individually, file-by-file changes, key concepts for a beginner, upstream vs modified comparison, tests, actual metrics, errors, security, Q&A with answers and next-step handoff. Even if blocked, the report must explain what was attempted and what remains.
6. **Quality gate.** Run the smallest meaningful tests, lint/type checks where applicable, and relevant original regression tests. Never call a failing or skipped check 'passed'. Document exact commands, exit codes and observed values.
7. **Efficient scope.** Two engineers / eight weeks. Prioritize a real ASR train→evaluate→approve cycle and integrated prototypes for other advanced features; do not claim that a mere annotation UI means every neural network retrained.


## Response after completing this specific step
State: status; actual changed files; important behavior difference; tests and metrics with numeric results; report path; blockers; next safe command. **Do not continue to the next step automatically.**
