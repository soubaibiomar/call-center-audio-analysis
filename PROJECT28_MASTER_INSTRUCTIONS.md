# PROJECT28_MASTER_INSTRUCTIONS — GPT-6.1 Sol (Medium)

## Mission
Upgrade the actual source repository https://github.com/ANI-IN/Call-Center-Intelligence-System into the eight-week two-developer **Adaptive Call Center Intelligence** research-grade MVP: batch and browser-live audio analysis (Whisper/Qwen3-ASR, real pyannote diarization, emotion model), LangGraph structured QA and compliance, RAG with citations, optional human-approved live suggestions, evidence-grounded coaching, and versioned verified human feedback leading to a demonstrable ASR train→evaluate→approve→rollback loop. Other neural families receive review and training interfaces, but do not claim they all improved within eight weeks.

## Invocation procedure — ONE STEP AT A TIME
1. Clone/fingerprint upstream and inspect actual code before using any prompt.
2. Open exactly one `prompts/STEP_XX_*_PROMPT.md` and its matching `report_templates/STEP_XX_*_REPORT.md`.
3. Complete tasks, tests and report for that single step; stop, summarize and present evidence for review.
4. Save the report at the exact `docs/implementation/STEP_XX_*_REPORT.md` path **inside the working repository**; replace templates' `NOT EXECUTED` blocks with actual evidence. Revisit reports if follow-on implementation changes them.
5. Each report must explain *what, why, how, original code, modified code, files, imports, architectural concepts, line-level code, tests, numerical analytics, Q&A with answers, risks and next dependency*.
6. New work must preserve the original Gradio and its QA/security/reporting behavior until a tested replacement exists.


## Non-negotiable approved visual design — read first for every step
- **Approved reference:** `design/APPROVED_GREEN_ERP_REFERENCE.png`; **implementation guide:** `design/UI_DESIGN_SYSTEM.md`; **evidence gates:** `design/UI_ACCEPTANCE_CHECKLIST.md`. Read all three before UI changes.
- The user rejected earlier blue/pink designs and approved a **light-sidebar, warm-white/off-white, forest/emerald green ERP design inspired by DJIN ERP**, with clean typography, white cards, subtle borders, status colors and purposeful charts. The approved design replaces prior UI styling suggestions without changing functional scope.
- **Forbidden:** blue or pink as theme, nav selection, interactive color, chart accent, link or decorative gradient. Use real accessible green/neutral styles with semantic amber/red for warnings/errors. Audit third-party component/chart default palettes.
- Shared shell across routes; responsive behavior; contrast, keyboard and reduced-motion checks. No fake numeric metrics or fabricated real-time/training states. All actual screens must be verified against the reference when browser tools are available.
- Frontend steps 22–31, 35–38, 42, 44–45 especially must implement/validate the approved UI; backend and ML steps must define the data and loading/error states needed to support it. Keep the original Gradio implementation as regression evidence.
- Each step report adds **section 13: Approved ERP UI design / visual contract verification**. Mark `Not applicable` with reason for backend-only tasks.

## Environment
- Windows 11, PowerShell, VS Code, Git, uv with isolated venv (no Conda), Docker Desktop, NVIDIA RTX 4060 8 GB.
- Existing Ollama in Docker must not be stopped/reconfigured automatically.
- Never push, purchase, expose/alter private datasets, commit secrets, or start external public deployments without user approval.
- No network/model/dataset access available? Execute safe local portions and document blockers rather than hallucinate success.

## Operating contract
## Global engineering and truthfulness rules

1. **Execute, do not only explain.** Inspect repository state before edits, then implement only the named step. If tooling is missing, report the exact blocker and non-destructive workaround; never invent commands, test results, file changes or benchmarks.
2. **Protect upstream compatibility.** Record `git rev-parse HEAD`, baseline branch, and the actual existing symbols/files before changing anything. Source locations listed in this prompt are candidates; confirm they exist at the pinned SHA. Preserve Gradio, LangGraph, faster-whisper, QA weighting, PII handling, caching, audit and PDF/JSON until replaced by tested alternatives.
3. **Work safely.** Do not delete data; overwrite work; modify unrelated services; push commits; deploy public services; buy resources; expose tokens; or download large datasets/models without explicit authorization. Use synthetic/consented fixtures only. Data allowed for analysis is not automatically permitted for model training.
4. **Hardware discipline.** Windows + PowerShell + VS Code + `uv` (not Conda), Docker Desktop, NVIDIA RTX 4060 8 GB, existing Ollama. Prefer CPU-first smoke checks and one GPU-heavy operation at a time; report measured peak VRAM.
5. **One step, one durable report.** After the attempt, replace the matching Markdown template under `docs/implementation/` with a **factual completed or blocked report** in English. Include code and imports explained individually, file-by-file changes, key concepts for a beginner, upstream vs modified comparison, tests, actual metrics, errors, security, Q&A with answers and next-step handoff. Even if blocked, the report must explain what was attempted and what remains.
6. **Quality gate.** Run the smallest meaningful tests, lint/type checks where applicable, and relevant original regression tests. Never call a failing or skipped check 'passed'. Document exact commands, exit codes and observed values.
7. **Efficient scope.** Two engineers / eight weeks. Prioritize a real ASR train→evaluate→approve cycle and integrated prototypes for other advanced features; do not claim that a mere annotation UI means every neural network retrained.


## Documentation quality contract
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
13. UI design contract verification: original vs new behavior, approved screenshot comparisons, styles and responsive/accessibility evidence or justified Not applicable.


## Project assignment and dependency rules
- **Developer 1 (AI/ML):** ASR/dataset/evaluation/pyannote/emotion/Qwen/LangGraph/RAG intelligence/active learning/finetuning/MLflow science.
- **Developer 2 (Platform):** FastAPI/PostgreSQL/Redis/S3 frontend/WebRTC/WebSocket, auth/CI/testing/deployment.
- PR review by the other developer. Write tests with every meaningful feature. Keep scope bounded.
- Some steps run in parallel once their inputs and API schemas are ready. Respect dependency checks rather than forcing artificial linear execution.
- Favor modular monolith + isolated workers for MVP, not a premature Kubernetes deployment.

## Definition of Done for the whole project
A reviewer can run a consented two-browser call, see incremental transcription and grounded suggestions, analyze historical audio and generate reports, correct transcripts and QA, view cautious emotion output, use knowledge search and coaching, and inspect a *real* ASR candidate fine-tuning/evaluation/promotion-or-rejection record. The documentation includes real measurements, security limitations, and complete provenance. Anything beyond that is explicitly labeled experimental/not validated.

---

## Approved UI Reference — Mandatory Override
Use the image `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png` as the primary design reference for all frontend work.
This replaces earlier UI direction.

### Mandatory visual rules
- Use a **light neutral ERP/SaaS look** inspired by the approved reference.
- Main colors: white, soft gray, green accents, dark green secondary emphasis, black/charcoal text.
- Avoid blue and pink as dominant brand colors.
- Cards must be rounded, spacious, and minimalist.
- Sidebar and top search/profile bar must follow the same structural spirit as the approved reference.
- The design should feel premium, modern, quiet, and business-oriented.
- Do **not** clone the original brand identity from the reference image; adapt the style to the product brand **Adaptive Call Center Intelligence**.

### Frontend acceptance rule
Any frontend-related task is incomplete unless its report includes:
1. screenshots,
2. a comparison against the approved reference,
3. used color tokens,
4. explanation of differences,
5. UI acceptance checklist results.
