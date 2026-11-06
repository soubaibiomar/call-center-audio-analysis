# Step 12 — Inventory datasets and build permission-aware splits

> **Execution status:** NOT EXECUTED — template; to be completed only after the coding agent performs this step.  
> **Scheduled:** W1–W3 | **Lead:** ML  
> **Upstream:** https://github.com/ANI-IN/Call-Center-Intelligence-System  
> **Prompt:** `prompts/STEP_12_inventory_datasets_and_build_permission_aware_splits_PROMPT.md`  
> **Actual report destination inside working repository:** `docs/implementation/STEP_12_inventory_datasets_and_build_permission_aware_splits_REPORT.md`

## 1. Goal and plain-English explanation
**Purpose:** Establish legal, reproducible training and evaluation corpora.

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
- `ml/datasets/`
- `docs/data/DATASET_CATALOG.md`
- `docs/data/ANNOTATION_GUIDE.md`

After work, create a table: `path | created/modified/kept | purpose | important exports | call sites | how tested`.

## 4. Code explanation and algorithm
- Meaningful code excerpt #1: *NOT IMPLEMENTED*.
- Inputs/outputs, typed schemas and validation: *NOT VERIFIED*.
- Algorithm/data flow, time/space/resource tradeoffs: *NOT VERIFIED*.
- Exceptions, failure handling and tests: *NOT VERIFIED*.
- Annotate nontrivial code line-by-line or by small logical blocks after implementation.

## 5. Imports and dependency explanation
**Relevant concepts/dependencies to investigate (do not assert these were installed):**
- **Hugging Face datasets** — confirm relevant symbols/versions and explain every import introduced.
- **Parquet** — confirm relevant symbols/versions and explain every import introduced.
- **data provenance** — confirm relevant symbols/versions and explain every import introduced.
- **speaker-disjoint splitting** — confirm relevant symbols/versions and explain every import introduced.

After execution list each **actual new import**: `import statement | library origin | symbol meaning | call site | reason | version | risks/alternatives`.

## 6. Core concepts explained for a beginner
**Concepts to teach with a concrete example:** Hugging Face datasets, Parquet, data provenance, speaker-disjoint splitting.

After work give definitions, one simple trace/example, comparison of alternatives and why the choice fits an 8-week, 2-person build.

## 7. Data structures, ML evaluation, security and privacy
- Dataset/model/input schema: NOT VERIFIED.
- Legal or consent limitations: must be explicitly reviewed.
- PII, access controls and threat handling: NOT VERIFIED.
- Train/validation/test leakage and model lineage (where relevant): NOT VERIFIED.

## 8. Tests, exact outputs and verification
- [ ] Manifest validates without audio
- [ ] Splits have no leaked speaker/call IDs
- [ ] Restricted files excluded from Git

| Command | Environment | Exit code | Passed | Failed | Skipped | Observed result |
|---|---|---:|---:|---:|---:|---|
| NOT RUN | — | — | — | — | — | Never invent evidence |

## 9. Analytics and quantitative report
- Hours per language: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).
- license coverage %: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).
- label agreement: record baseline, actual, sample size, conditions, formula and interpretation (or Not measured).

Do not present targets or examples as results. Include definition, sample size, benchmark dataset, CPU/GPU, p50/p95 if applicable, comparison with baseline, and uncertainty.

## 10. Questions with answers (conceptual starter set)
1. **Q:** Why must licenses be tracked per subset?  
   **A:** Aggregated datasets can combine incompatible rights.
2. **Q:** Why speaker-disjoint splits?  
   **A:** Shared speaker characteristics can inflate test accuracy.
3. **Q:** How handle Darija script variation?  
   **A:** Agree on normalization rules before calculating WER.
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
