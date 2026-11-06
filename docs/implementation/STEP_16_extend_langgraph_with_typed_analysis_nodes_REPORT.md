# STEP_16 — Extend LangGraph with typed analysis nodes

**DONE — PASS WITH LIMITATIONS.** 2026-10-28, Africa/Casablanca. Owner: ML engineering. Branch `feature/project28-foundation`, HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`, pinned upstream `fed4b610742c1337147281fcec8f2cdcc0a79be5`. Windows, PowerShell, uv-managed Python. No training, deployment, commit or push.

## 1. Objective and prerequisites

Completed reusable evidence, intent, resolution and review-policy nodes around the existing summary/weighted-QA/report pipeline. STEP_15 remains a research prototype with the separately saved audio limitations; none is claimed resolved here. No new model or corpus was required for deterministic policy nodes. Intent/resolution are explicit English phrase heuristics with Unknown/ambiguous outcomes, not trained classifiers.

## 2. Actual upstream versus upgraded implementation

| Behavior | Pinned upstream | Working implementation |
|---|---|---|
| Post-redaction graph | Direct summary/QA edge | Evidence → intent → resolution → existing summary/QA → deterministic review policy |
| Role of resolution | LLM summary classification | Summary remains; independent phrase evidence can flag unsupported/conflicting resolution for review |
| Review route | Critical compliance only | Critical compliance, missing/invalid evidence, low confidence, unsupported resolution |
| Reports | Existing report structure | Optional typed `analysis_review` stores source excerpts, timestamps, decisions and reason codes |
| Tracing | Raw-node trace decorators and compiled graph returned | Application `PrivateWorkflow.invoke` disables remote tracing around graph execution; existing content-free model-run observations retained |

Inspected upstream workflow using `git show`. Scoped tracked diff at inspection: 3 files, 129 insertions and 47 deletions; this includes preserved earlier changes. New untracked modules are not included by ordinary `git diff`. Existing intake, ASR, PII/injection checks, QA weights, exports and persistence remain. Existing synthetic happy-path fixture now contains explicit resolution wording so the stricter policy can accept its resolved summary.

## 3. Files

- `src/graph/analysis_nodes.py`: typed evidence/review and pure collection/classification/policy functions.
- `src/graph/workflow.py`: separate graph nodes, policy edge, retry/timeout validation, privacy wrapper and report attachment.
- `src/graph/state.py`: optional `CallReport.analysis_review` for additive backward-compatible report JSON.
- `tests/unit/test_analysis_nodes.py`: evidence/Unknown, absent evidence, phrase evidence, review decisions, provider-input redaction and tracing context.
- `tests/integration/test_pipeline_end_to_end.py`: supported-resolution baseline fixture.
- `docs/api/openapi.json`: regenerated schema for additive report contract.
- This report, progress tracker and `evidence/step16-20261028/policy-benchmark.json`.

## 4. Code and data flow

`collect_review` copies finite, nonnegative, positive-length source segments after redaction. Invalid timestamps, absent source evidence and low confidence add stable reason codes. `classify_intent` matches explicit billing, technical-support or cancellation patterns; exactly one category produces an intent and indices into evidence. `classify_resolution` uses explicit resolved, unresolved or escalation wording with the same ambiguity rule. These are lexical indicators: negation, sarcasm, complex context and languages beyond the narrow patterns need review and can be misclassified.

`decide_review` compares independently matched resolution with the summary candidate, adds `unsupported_resolution` for unknown/disagreement and preserves critical-compliance review. The graph routes analysis failure to the existing error node, review-required results to supervisor report creation, and accepted results to normal reporting. Both report nodes attach the typed record; supervisor reports set their own status to flagged_for_review. Report JSON persistence retains the record; no new event table, human notification or review UI is implemented.

Graph construction rejects attempt budgets outside 1–5 and provider timeouts outside 1–600 seconds. Existing `invoke_validated` handles finite attempt counts, schema rejection, provider failures, timeout classification and sanitized observations. Timeout is the provider-request timeout, not hard cancellation of arbitrary model code or a global workflow deadline. Deterministic nodes make no external calls and need no retry layer.

`PrivateWorkflow.invoke` wraps graph invocation in `tracing_context(enabled=False)` so application graph inputs do not get sent to remote LangSmith tracing through this boundary. Direct use of `build_workflow` or access to the underlying graph is outside this application guard. Redaction remains dependent on the existing detector's coverage.

## 5. Imports and dependencies

LangGraph 0.4.1 provides the existing `StateGraph` and compiled graph. Pydantic 2.11.3 supplies `BaseModel`/`Field` for typed data and default lists. New standard imports: `math` for finite timestamps, `re` for explicit phrase matching, `Literal` for enumerated states, and `TYPE_CHECKING`/postponed annotations to avoid the state-contract import cycle. Workflow uses `Any` at the dynamic invocation boundary and installed LangSmith `tracing_context` to disable content tracing. Local imports connect the new contracts and policy functions. No package dependency was added.

## 6. Concepts

Typed state defines what one graph stage may pass to another. Evidence is an excerpt plus source timing, not proof that an interpretation is semantically true. Policy rules are deterministic and cannot be overruled by the summary model. Example: a summary claiming resolved without a recognized resolution cue becomes a supervisor review result. Unknown and conflicting evidence are explicit outcomes rather than invented certainty.

## 7. Security and reliability

Injection detection precedes redaction and model calls; redaction precedes all new evidence and both summary/QA calls. Tests capture provider-bound transcript objects and verify a synthetic email is absent in both. This is fixture evidence, not a claim that every PII category is detected. Typed reports contain redacted excerpts and must retain existing access controls. Existing model-run metadata remains content-free. Current audio security and evaluation limitations are in `CURRENT_LIMITATIONS.md` and remain open.

## 8. Actual verification

The first expanded baseline run correctly flagged its unsupported resolved summary, exposing the fixture mismatch. The fixture was changed to include explicit resolution wording. A Windows default text-encoding read also failed; UTF-8 file handling corrected that edit. Ruff and formatting then passed; mypy passed on the three graph source files.

Focused summary/QA/security/inference run: **68 passed in 6.06 seconds**. Full service-configured suite: **389 passed, one warning, in 50.63 seconds**. The subsequently added tracing-boundary check and finite-timestamp guard were covered by the final graph-focused run: **5 passed in 1.36 seconds**; an earlier focused graph/integration run passed 7 tests. No claim is made that the full suite was rerun after those final narrow changes. API schema was regenerated and included in the full suite. No real model/provider inference was performed in STEP_16; pipeline tests use mocks and synthetic data.

## 9. Metrics

Executed 100 synthetic deterministic collect/intent/resolution/review chains: mean 0.0683 ms, nearest-rank p95 0.0987 ms on this local run. Evidence: `evidence/step16-20261028/policy-benchmark.json`. This is the policy chain, not individual model-node p95. Operational graph success %, model-node p95 and real invalid-JSON rate are **Not measured**; no improvement claim or population accuracy is inferred from test counts.

## 10. Questions and answers

1. Why deterministic nodes? They permit repeatable policy without extra autonomous model calls.
2. Why Unknown? Missing or ambiguous cues do not justify a categorical outcome.
3. Is phrase matching reliable semantic inference? No; it is a narrow prototype and must be evaluated for negation and other contexts.
4. Can the model bypass review? The route is controlled by policy outside its output.
5. Why disable graph tracing? Initial graph state includes audio and metadata that should not be exported to remote tracing.
6. Are retries globally bounded? Attempt counts are finite per inference; provider timeouts are bounded, but there is no hard total workflow deadline.
7. Does the record notify a human? It persists review state in report JSON; notification and human review UI are future work.

## 11. Decisions and limitations

Use conservative lexical policies, preserve weighted scoring, and attach additive review data. Unknown resolution now increases review volume; this behavior change is deliberate and documented. Intent is English-only and coarse; evidence matching is not semantic entailment and does not validate every QA justification. Human-review notifications, comprehensive external-leak testing, a global graph deadline, production model benchmarks and streaming privacy remain future work.

## 12. Handoff

- [x] Typed evidence, intent, resolution and review-policy graph stages.
- [x] Baseline graph completion and deterministic review/error routing tested with synthetic data.
- [x] Existing finite inference attempts/timeouts validated; security/weighted-QA regression tests pass.
- [x] Additive report persistence and API schema updated.
- [x] Synthetic measurements labeled honestly.

**Next eligible step: STEP_17**, subject to its knowledge-ingestion and rights prerequisites. No STEP_17 work was started.

## 13. Approved ERP UI design / visual contract verification

No frontend changed; screenshots and style/accessibility checks are not applicable. Existing report JSON gains optional typed evidence times, intent/resolution Unknown states, review reasons and evidence indices. The future summary/QA panels can display these without presenting unsupported claims as verified facts. The original Gradio remains, and new frontend work must use the approved `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`.
