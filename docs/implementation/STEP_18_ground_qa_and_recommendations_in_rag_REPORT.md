# STEP_18 — Ground QA and recommendations in RAG

**DONE — PASS WITH LIMITATIONS (internal extractive prototype)**. Owner ML / Codex; 2026-10-29, Africa/Casablanca. Windows/PowerShell, uv Python 3.12, local PostgreSQL pgvector. Branch `feature/project28-foundation`, working HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`; upstream `fed4b610742c1337147281fcec8f2cdcc0a79be5`. No commit or push. This replaces the initial partial report.

## 1. Goal and completed work

Added conservative policy evidence to the analysis graph and QA/compliance output. The graph runs retrieval after redaction, returns a cited policy excerpt or explicit abstention, and preserves the result in QA and final reports. No free-form company procedure is generated. Existing rubric scores retain their original meaning; the policy reference does not claim that an agent complied with it.

Reviewed master instructions, STEP_17 report and limitations, STEP_18 prompt/template, current graph, QA rubric, schemas and injection detector. STEP_17 provides the prerequisite internal knowledge store. Production authentication and deployment remain inherited limitations; server-side identity is bound when constructing the service rather than accepted from graph input.

## 2. Actual upstream versus upgraded implementation

| Capability | Upstream / preceding implementation | Current symbol and behavior |
|---|---|---|
| Policy retrieval | Upstream QA rubric has no knowledge retrieval; STEP_17 has isolated store | `GroundedPolicyService.from_store` binds scoped SQL retrieval and local embedding callback |
| Graph integration | Resolution went directly to summarization/QA | `knowledge_step` runs between those nodes after PII redaction |
| QA evidence | Rubric scores only | `QAScoreResult.policy_evidence` adds source/abstention; no automatic score changes |
| Reports | Existing analysis/model metadata | `CallReport.policy_evidence` persists the same typed result |
| Policy date | STEP_17 expiry only | `Document.effective_at` optional; undated/future documents cause abstention |
| Source validation | Initial exact excerpt checker | Checks permissions, expiry, effective date, citation, excerpt and known injection patterns |

Ordinary tracked Git diff includes earlier uncommitted changes. This step changes state/workflow and adds or extends knowledge files, tests and documentation. Untracked files do not appear in normal diff statistics. No upstream behavior was removed. Whole-workspace diff evidence is saved alongside this report; it must not be attributed entirely to STEP_18.

## 3. Files and interfaces

- `services/knowledge/grounding.py`: `PolicyEvidence`, `PolicyAnswer`, exact checker and scoped retrieval service.
- `services/knowledge/ingestion.py`: optional timezone-aware effective date, compatible with old stored JSON; undated documents remain searchable but cannot produce supported policy answers.
- `src/graph/workflow.py`: optional service injection in build/compile, new graph node, QA/report propagation.
- `src/graph/state.py`: additive optional policy evidence in QA and report contracts.
- `tests/rag/test_grounding.py`: validation, adversarial graph-node cases and actual database deletion/retrieval test.
- `docs/benchmarks/RAG.md`: benchmark scope and interpretation.
- Report, progress tracker and `evidence/step18-20261029/`: factual execution records and repeatable fixture.

## 4. Important code and data flow

`from_store` captures trusted tenant, department, role and encoder revision. Its closure embeds the redacted query and invokes SQL permission-filtered search with limit two. Fetching two instead of one lets the service abstain on competing evidence. This conservatively treats any multiple hits as potentially conflicting rather than claiming semantic contradiction detection.

`answer` bounds query length, catches retrieval failure without exposing connection errors and abstains for zero/multiple passages. The checker repeats permission checks, requires a real effective date no later than current time and rejects known injection signatures. Citation ID must match and the output must be an exact substring of the source. Successful answers include passage, source ID and effective date; uncertainty is represented by explicit abstention with a reason.

The graph receives the service through trusted construction, never through a user-provided state field. Its node executes after redaction and before summarization/QA. QA receives the result as a separate typed annotation after its original scoring call. Both ordinary and supervisor reports preserve it. Source content is never passed to the LLM or dispatched as commands/tools. Missing service configuration produces abstention without breaking the baseline workflow.

## 5. Imports and dependencies

No new package was installed. Standard-library `datetime/UTC` supplies aware evaluation time, `UUID` tenant identity, `Callable` typed retrieval/embedding callbacks and `Literal` answer states. Pydantic `BaseModel/Field` supplies serialized contracts and an independent default sources list. Local `Chunk/permitted` reuse source/access validation, `KnowledgeStore` supplies typed SQL integration and `detect_injection` reuses existing signature detection. Graph/state import the service/result types. Tests use datetime/timedelta/uuid4 fixtures, pathlib/os private URL-file configuration, pytest skip/assertions and psycopg for actual isolated PostgreSQL. Benchmark json/Path serialize only synthetic outputs. Existing versions remain Pydantic 2.11.3 and psycopg 3.3.6; no runtime/training dependency changed.

## 6. Concepts and tradeoffs

RAG retrieves external knowledge at inference time; it does not update neural weights. Citation grounding identifies where a statement came from. Exact extraction proves that the quoted passage occurs in the retrieved source; it does not establish policy applicability or that the agent followed it. For example, a refund query can return the authorized policy excerpt with its ID; no source means an abstention, never an invented procedure.

The extractive design offers a simple boundary against generated policy hallucinations. It sacrifices synthesis and often abstains when multiple passages are retrieved. Exact search and single-source acceptance are prototype choices rather than a production recall guarantee.

## 7. Data, security and reliability

All new fixtures are synthetic. No training or new model download ran. STEP_17 already validated actual local BGE-M3 embeddings; this step tests wiring with injected vectors and deterministic retrieval fixtures. Queries are redacted by the graph first. Direct service callers must supply approved non-sensitive queries themselves.

Document text cannot invoke a tool because no model/tool execution exists in this path. Signature detection is additional screening, not a complete injection detector: unknown malicious wording may still be displayed as quoted evidence. Consumers must render it as untrusted text. Authorization is trusted server configuration; production HTTP auth/RLS, retention erasure and archival history remain STEP_17 limitations. A deletion after the retrieval transaction can race a response; snapshot consistency is not continuous revocation. Expired/future/undated or ambiguous sources abstain.

## 8. Verification

Commands: `.venv/Scripts/python.exe -m pytest tests/rag -q --tb=short`, Ruff on changed knowledge/graph/test files, and `mypy services/knowledge`. With the isolated knowledge URL configured: **12 passed in 1.44 seconds**, no skips. Mypy passed five source files. Ruff passed after formatting and fixing imports/types. Focused graph/regression run: **4 passed in 2.01 seconds** after QA propagation. Earlier graph/analysis checks: eight passed.

The actual PostgreSQL test verifies scoped service construction, supported retrieval and abstention after deletion. Synthetic cases cover valid evidence, wrong citation, invented excerpt, tenant mismatch, expired evidence, future/undated policy, competing policies, missing evidence and known malicious instructions. The graph node is exercised and existing end-to-end tests pass. Full regression result is recorded in the completion note below. Warnings concern existing pytest asyncio scope and dependency deprecations.

## 9. Benchmark evidence and limits

Executed `.venv/Scripts/python.exe .local/step18-benchmark.py`; archived runnable script and `benchmark.json` are in the evidence directory. Four synthetic outcomes: one supported source, missing evidence, contradictory passages and known malicious content. **Exact citation support 100% (1/1 emitted answer); unsupported emitted passages 0; three other cases abstained.** This is an extractive fixture, not semantic entailment evaluation or neural retrieval benchmarking. Retrieval recall@k, representative hallucination rate, baseline comparison, latency percentiles and peak VRAM: **Not measured**. No production quality improvement is claimed.

## 10. Technical questions and answers

1. **Does RAG retrain weights?** No. It fetches context; this implementation quotes it without generating policy text.
2. **How are conflicts handled?** Any multiple eligible hits abstain for human review. This may reject complementary documents; semantic reconciliation is future work.
3. **Why adversarial tests?** Retrieved sources are untrusted. Known attacks are rejected; architectural isolation prevents source text reaching tools even if screening misses one.
4. **Does the citation prove compliance?** No. It proves an excerpt matches one retrieved policy. The baseline rubric score is separate; agent-policy entailment is unmeasured.
5. **What if no provider is configured?** The graph records an explicit abstention, preserving baseline operation and avoiding unsupported policy advice.
6. **Can old documents work?** Their schema remains valid. They need a trusted effective date before producing supported policy references.
7. **How does deletion work?** Each call retrieves fresh SQL-filtered evidence; the database test deletes then queries again and obtains abstention. It does not solve races after retrieval or historical archives.

## 11. Decisions and remaining limitations

Accepted an integrated extractive prototype instead of free-form policy generation. Baseline scores remain unchanged and no retrieved passage enters an LLM prompt. Multiple hits require review. No automatically inferred effective date, entailment, threshold-tuned relevance, multi-source synthesis or production deployment is claimed. Existing knowledge/audio limitations remain. A deployment must construct a scoped `GroundedPolicyService.from_store(store, encoder.encode, revision=..., tenant_id=..., department=..., role=...)` and pass it to `compile_workflow(..., knowledge=service)`; default entry points abstain until configured.

## 12. Handoff and acceptance decision

**PASS WITH LIMITATIONS**, for the internal extractive evidence prototype. Sources accompany supported answers; missing sources abstain; retrieved content cannot direct tool execution in this path. STEP_19 is next eligible subject to its prerequisites and explicit user request. Generation/synthesis must preserve these boundaries and add representative semantic evaluation before claiming grounded automated policy judgments.

Evidence checklist: code implemented; positive/adversarial and real database tests executed; synthetic benchmark denominators disclosed; baseline graph retained; report/progress updated; no push or production migration.

## 13. Approved ERP UI design / visual contract verification

Backend contracts only; no frontend or route changed, so screenshots and visual/accessibility checks are not applicable. Optional source/passages/effective dates and abstention reasons support a future evidence panel. It must distinguish quoted policy from verified compliance, render source text as text and follow the approved green-neutral Commercially reference. Original Gradio remains; no redesigned screen or unsupported suggestion card was added.

### Final validation and schema correction

Earlier full run: **401 passed, 1 warning in 57.86s**. After the additive QA contract and database test, full run: **401 passed, 1 failed** in 57.99s; the sole failure was the stale saved OpenAPI specification. Ran `scripts/export_api_schema.py` to regenerate `docs/api/openapi.json` (additional modified file). The API now exposes the optional typed evidence field. The affected schema/knowledge/graph checks were rerun with the isolated DB configured; see `final-affected.txt`. An intermediate unconfigured run skipped its one DB test; that skip is not counted as passed. No source behavior changed after the full run apart from the saved schema correction. Mypy passed seven knowledge/graph source files; final Ruff passed.

The interface impact is additive API schema metadata; no rendered screen changed. Future clients can display policy evidence or abstention, while the current default service configuration still abstains.
