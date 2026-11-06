# Step 03 — Establish branching and collaboration conventions

> **Execution status:** NOT EXECUTED — template; to be completed only after the coding agent performs this step.  
> **Scheduled:** W1 | **Lead:** Platform  
> **Upstream:** https://github.com/ANI-IN/Call-Center-Intelligence-System  
> **Prompt:** `prompts/STEP_03_establish_branching_and_collaboration_conventions_PROMPT.md`  
> **Actual report destination inside working repository:** `docs/implementation/STEP_03_establish_branching_and_collaboration_conventions_REPORT.md`

## 1. Goal and plain-English explanation
**Purpose:** Enable two-person work with protected baseline and predictable integration.

**What was actually executed:** NOT EXECUTED — coding agent must write what it did with dates and commands.  
**Why it was necessary:** Document the concrete problem and user value.  
**What remains:** NOT EXECUTED.

## 2. Actual upstream vs your implementation
| Feature or code path | Upstream at pinned SHA (verified evidence) | Your actual change | Why it changed | Compatible? |
|---|---|---|---|---|
| To verify | Do not guess | Not implemented yet | — | Unknown |

Upstream SHA: `NOT RECORDED`  
Working branch/SHA: `NOT RECORDED`  
`git diff --stat`: `NOT RUN`

## 3. Files explained — created / modified / kept
These are **planned investigation targets**, not claims of created files:
- `.github/PULL_REQUEST_TEMPLATE.md`
- `docs/development/workflow.md`
- `docs/implementation/`

After work, create a table: `path | created/modified/kept | purpose | important exports | call sites | how tested`.

## 4. Code explanation and algorithm
- Meaningful code excerpt #1: *NOT IMPLEMENTED*.
- Inputs/outputs, typed schemas and validation: *NOT VERIFIED*.
- Algorithm/data flow, time/space/resource tradeoffs: *NOT VERIFIED*.
- Exceptions, failure handling and tests: *NOT VERIFIED*.
- Annotate nontrivial code line-by-line or by small logical blocks after implementation.

## 5. Imports and dependency explanation
**Relevant concepts/dependencies to investigate (do not assert these were installed):**
- **Git branching** — confirm relevant symbols/versions and explain every import introduced.
- **PR reviews** — confirm relevant symbols/versions and explain every import introduced.
- **protected branches** — confirm relevant symbols/versions and explain every import introduced.
- **CODEOWNERS (if desired)** — confirm relevant symbols/versions and explain every import introduced.

After execution list each **actual new import**: `import statement | library origin | symbol meaning | call site | reason | version | risks/alternatives`.

## 6. Core concepts explained for a beginner
**Concepts to teach with a concrete example:** Git branching, PR reviews, protected branches, CODEOWNERS (if desired).

After work give definitions, one simple trace/example, comparison of alternatives and why the choice fits an 8-week, 2-person build.

## 7. Data structures, ML evaluation, security and privacy
- Dataset/model/input schema: NOT VERIFIED.
- Legal or consent limitations: must be explicitly reviewed.
- PII, access controls and threat handling: NOT VERIFIED.
- Train/validation/test leakage and model lineage (where relevant): NOT VERIFIED.

## 8. Tests, exact outputs and verification
- [ ] Branch exists and does not modify main
- [ ] Template covers tests/security/docs
- [ ] No unauthorized push

| Command | Environment | Exit code | Passed | Failed | Skipped | Observed result |
|---|---|---:|---:|---:|---:|---|
| NOT RUN | — | — | — | — | — | Never invent evidence |

## 9. Analytics and quantitative report
- Git branch status: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).
- workflow rules count: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).
- unreviewed PR count: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).

Do not present targets or examples as results. Include definition, sample size, benchmark dataset, CPU/GPU, p50/p95 if applicable, comparison with baseline, and uncertainty.

## 10. Questions with answers (conceptual starter set)
1. **Q:** Why short-lived branches?  
   **A:** They minimize integration conflicts in a two-person project.
2. **Q:** What belongs in PR evidence?  
   **A:** Tests, changed files, migration notes and measured results.
3. **Q:** Is a Git branch a deployment?  
   **A:** No, deployment must separately select tested artifacts.
4. **Q:** What did the execution prove?  
   **A:** NOT YET EXECUTED — answer from observed tests after completion.
5. **Q:** What failed or remains uncertain?  
   **A:** NOT YET EXECUTED — enumerate blockers and evidence after completion.

## 11. Decisions, changes and risks
- Decision / alternatives / reason: NOT RECORDED.
- Risks, severity, mitigation and owner: NOT RECORDED.
- Remaining tasks/dependencies: NOT RECORDED.
- Any changed behavior from original: NOT VERIFIED.

## 12. Actual deliverables, next handoff and evidence checklist
- [ ] Changes actually executed and documented.
- [ ] Before/after paths grounded in source and Git diff.
- [ ] Code and every new import explained clearly.
- [ ] Actual tests, numeric results and failures logged.
- [ ] Minimum 5 answered Q&As retained and updated with runtime evidence.
- [ ] No secrets/PII or unlicensed training audio committed.
- [ ] Handoff specifies next dependency and exact command.

## 13. Approved ERP UI design / visual contract verification

**Approved reference:** `design/APPROVED_GREEN_ERP_REFERENCE.png` and `design/UI_DESIGN_SYSTEM.md`.  
**Status:** NOT EXECUTED. For backend-only work, provide an evidence-based `Not applicable` and explain the user-facing API/data contract.

| Check | Actual evidence / findings |
|---|---|
| Routes/components and files affected | NOT VERIFIED |
| Original Gradio vs upgraded interface: preserved/changed | NOT VERIFIED |
| Light sidebar, neutral canvas, forest-green accents, no blue/pink | NOT VERIFIED |
| Typography, spacing, chart legends, status labels, empty/loading/error states | NOT VERIFIED |
| Responsive layouts (1440/1280/1024/390 px) | NOT VERIFIED |
| Accessibility: contrast, keyboard, focus and reduced-motion | NOT VERIFIED |
| Real browser screenshot links (desktop / mobile) | NOT CAPTURED |
| Automated UI visual/e2e checks, counts and outcome | NOT RUN |
| Design review decision and deviations | PENDING |

**Explain technical implementation when applicable:** token definitions and selectors, each UI import and its purpose, shared component boundaries, color/contrast rationale, real interactions, rendering cost, evidence-based comparison with the approved screenshot, and remaining discrepancies. Never substitute the generated reference image for screenshots of an implemented application.

## UI Reference Compliance
- Was this step UI-related? If yes, compare the implementation with `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`.
- Screenshots:
- Matching elements:
- Intentional differences:
- Color tokens used:
- Accessibility notes:
- Remaining UI gaps:
