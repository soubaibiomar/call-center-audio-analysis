# STEP_17 — Create controlled company knowledge ingestion

Owner: Platform / Codex. Executed locally on 2026-10-28–29; report date 2026-10-29 (Africa/Casablanca). Status: **DONE — PASS WITH LIMITATIONS**, for the internal prototype boundaries below.

Branch: `feature/project28-foundation`. Working HEAD: `a37e4634af1d2947fc3c548d54e62bda0b0daf89`. Upstream: ANI-IN/Call-Center-Intelligence-System at `fed4b610742c1337147281fcec8f2cdcc0a79be5`. Changes remain uncommitted. Windows, PowerShell, uv Python 3.12, local Docker PostgreSQL and CPU BGE-M3 inference. No training ran.

## 1. Goal and plain-English explanation

Built a source-traceable internal knowledge library. A trusted administrator supplies an approved procedure and its permissions; the library extracts bounded text, creates cited chunks, embeds them locally and stores them in PostgreSQL. Retrieval returns only matching tenant, department, role, expiry and embedding revision. Updating a document replaces its active chunks atomically. Deleting it removes its chunks.

Read the master instructions, STEP_INDEX, full STEP_17 prompt/template, preceding STEP_16 report and current limitations. STEP_16 records completion with limitations and STEP_17 eligibility. Synthetic procedures avoid importing unapproved company/customer data. This step does not add an HTTP endpoint, approval UI or RAG generation. It supplies tested Python interfaces for the next step.

## 2. Actual upstream vs implementation

`git ls-tree -r --name-only fed4b610742c1337147281fcec8f2cdcc0a79be5 -- services/knowledge tests/rag` returned no files. These directories are additions, not upstream functionality renamed or replaced.

| Capability | Actual upstream | Upgraded path / symbol | Behavior and compatibility |
|---|---|---|---|
| Company document contract | No knowledge module | `services/knowledge/ingestion.py:Document` | Explicit tenant, department, roles, version, approval, retention and source |
| Provenance and extraction | No knowledge module | `extract_chunks`, `Chunk` | UTF-8 TXT/Markdown; section, nullable page, digest and versioned citation |
| Neural embeddings | No knowledge module | `services/knowledge/embeddings.py:BgeM3` | Offline pinned 1024-dimensional dense embeddings |
| Search and persistence | No knowledge module | `services/knowledge/store.py:KnowledgeStore` | Exact cosine ranking of authorized active chunks |
| Update/delete validation | No RAG tests | `tests/rag/` | Real pgvector tests plus isolated schema/extraction tests |
| Original audio/Gradio/graph | Existing upstream code | No STEP_17 edits to these paths | Existing workflow retained; no knowledge generation injected yet |

Whole-workspace `git diff --stat` recorded 40 tracked files, 972 insertions and 367 deletions, mostly accumulated earlier steps. `git diff` does not include untracked additions. Both tracked diff outputs and the STEP_17 untracked inventory are saved in [evidence](evidence/step17-20261029/). Do not attribute that entire accumulated diff to STEP_17.

## 3. Files explained — created / modified / kept

| File | Change | Purpose and interface |
|---|---|---|
| `services/knowledge/__init__.py` | Created | Package boundary; no import-time connection/model load |
| `services/knowledge/ingestion.py` | Created | Typed document/chunk inputs; bytes to chunks; independent permission predicate |
| `services/knowledge/embeddings.py` | Created | Absolute local path and pinned revision to bounded batches of vectors |
| `services/knowledge/store.py` | Created | Injected psycopg connection; explicit setup, replace, search and delete |
| `tests/rag/test_ingestion.py` | Created | Provenance, grants, invalid vectors, invalid inputs and weight-integrity rejection |
| `tests/rag/test_store.py` | Created | Dedicated real `knowledge_test` database ACL/update/delete checks; 10-second connection timeout |
| `docs/development/knowledge-local.md` | Created | Setup boundary, local entry points, deployment limitations |
| `docs/implementation/evidence/step17-20261029/` | Created | Numeric evaluation, repeatable script, Git snapshots and regression log |
| This report, `PROGRESS.md` | Created / updated | Execution results and next-step handoff |

Private runtime configuration, downloaded model and temporary download scripts remain in ignored `.local/`. No root production dependencies or migrations were modified for this step. Proposed `services/api/routes/knowledge.py` was not created because this prototype has no authenticated public ingestion workflow.

## 4. Code explanation and algorithm

`Document` validates UUID identities, nonempty department/source, recognized nonempty role grants, positive version and timezone-aware expiry. Approval defaults false. `Chunk` carries a document snapshot, ordinal, section, optional page, text, full content hash and citation.

`extract_chunks` first rejects unapproved/expired inputs, unsupported extensions and inputs over 2 MiB. Strict UTF-8 decoding rejects malformed encoding; control-byte validation rejects obvious binary payloads. It treats Markdown as plain text, never executing markup. Heading changes flush the buffer and record a section. Long lines are split; ordinary lines accumulate up to the chosen character budget. `emit` strips empty text, hashes normalized bytes and creates `documentUUID:vVERSION:ordinal:hashPrefix`. For TXT/Markdown, page is null because no real page coordinates exist. Extraction is linear in input length with bounded input size. Character chunks may exceed the token budget in some scripts; embedding rejects them explicitly rather than truncating content.

`BgeM3.__init__` requires the approved revision and an absolute local directory, streams SHA-256 over the downloaded checkpoint, and rejects mismatch before loading torch. Local-only tokenizer/model loading prevents inference-time downloads; remote model code is disabled and checkpoint loading requests weights only. `encode` validates batch size 1–16 and text lengths, rejects more than 512 tokens, runs inference without gradients, takes CLS representations and normalizes them. The 1024-dimensional output is checked. This is dense inference, not sparse or multi-vector BGE retrieval and not training.

`vector_literal` rejects wrong dimensions, NaN, infinity, overflowed norms and effectively zero vectors before serialization. Values remain bound SQL parameters. `initialize` creates pgvector and composite-tenant document/chunk tables only on explicit administrative invocation. The foreign key cascades chunk deletion. `replace` validates all vectors before mutation, takes a transaction advisory lock for the tenant/document, rejects stale versions, and deletes/inserts within one transaction. A failure rolls back the replacement. Only the latest version remains.

`search` joins documents/chunks and filters tenant, exact department, role grant, approval, expiry and model revision inside SQL. Cosine distance orders only eligible results; limit is 1–20. There is no administrator bypass. `delete` binds tenant plus document ID. Non-autocommit callers must commit. These are trusted Python administrative interfaces: caller-supplied identity is not an authentication mechanism.

## 5. Imports and dependencies

| Actual imports | Origin / role | Why and tradeoffs |
|---|---|---|
| `__future__.annotations` | Python stdlib | Forward reference from validator to Document |
| `hashlib` | stdlib | Chunk provenance and pinned model integrity; streaming avoids loading checkpoint just to hash |
| `datetime.UTC, datetime` | stdlib | Consistent approval/expiry enforcement; tests also use timedelta |
| `pathlib.PurePath, Path` | stdlib | Extension inspection and explicit local model paths |
| `typing.Literal` | stdlib | Restricts role names |
| `uuid.UUID` | stdlib | Tenant/document typed identity; tests/evaluation use uuid4 |
| `pydantic.BaseModel, Field, model_validator` | Pydantic 2.11.3 | Input/schema validation and JSON serialization; alternatives would require manual validation |
| `importlib` | stdlib | Optional lazy torch/transformers imports; ordinary API tests need not load neural runtime |
| `json` | stdlib | Decode stored chunk payloads when connection does not already return dictionaries |
| `math` | stdlib | Finite embedding and norm checks |
| `psycopg` | Third party 3.3.6 | Transactional PostgreSQL, bound parameters; no separate vector Python adapter needed |
| `torch`, `transformers` (dynamic imports) | Local optional runtime 2.14.1 / 4.57.6 | Inference mode, normalization, AutoTokenizer and AutoModel; avoids hosted embedding transfer |
| `services.knowledge.ingestion.Chunk, Document` | Local | Reuse authoritative contracts in storage |
| `pytest`, `os`, fixture helpers | Pytest / stdlib | Assertions, private URL-file configuration, synthetic temporary files and UUIDs |
| `BgeM3`, `extract_chunks`, `permitted`, `vector_literal`, `KnowledgeStore` | Local test imports | Exercise public contracts directly |
| `time`, `json`, `Path`, `uuid4`, datetime helpers, psycopg and service classes | Evaluation script | Timings, reproducible synthetic data, persisted evidence and actual local neural/DB calls |

pgvector server extension: **0.8.7**. Dedicated image `pgvector/pgvector:pg17`, observed digest `sha256:ac08538c6f8b9904c33c8224c5e5706dbe760aca29db1d096972b4052c22a75d`. Model loading uses existing optional ASR runtime; psycopg and hf-xet were added there using uv. No Conda. Sentence-transformers/FlagEmbedding were not added: direct normalized CLS inference follows the official BGE dense example. Hugging Face hub 0.36.2 was used for provisioning, not hosted inference. No new dependency is used for training.

## 6. Concepts explained from first principles

An embedding represents text as a list of numbers. Similar policy/query meanings should have nearby vectors; cosine distance compares their directions. pgvector lets PostgreSQL store those vectors beside permission metadata. Exact search examines eligible vectors rather than using an approximate nearest-neighbor index: simple and correct for this small prototype, with linear scaling costs.

Chunking splits a procedure into retrievable passages. Provenance identifies the exact version and passage: a refund answer can cite the source rather than merely claiming a policy exists. Model revision is separate from document version because a new encoder may assign different coordinates to the same words. An ACL is a list of explicit grants; tenant, department and role must all match. A transaction makes replacement all-or-nothing, avoiding partially indexed versions.

## 7. Data, model, security and reliability

Three synthetic procedures and two synthetic questions were used; no company secrets, customer recordings or personal information were embedded. Input source approval must come from a trusted administrator; the library does not independently establish ownership or consent. Do not feed its configuration directly from unauthenticated client parameters.

Model: [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3), MIT model card, pinned revision `5617a9f61b028005a4858fdac845db406aefb181`. Downloaded checkpoint: 2,271,145,830 bytes; SHA-256 `b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38`, verified at assembly and loading. Configuration/tokenizer files were provisioned at that revision; only the checkpoint is independently runtime-hashed. CPU inference, no gradient updates, no GPU/peak-VRAM measurement.

PostgreSQL test service binds loopback port 5547. Credentials remain ignored. Main application PostgreSQL was not altered to enable pgvector. Database ACL filtering is tested, but the development database account is privileged; this is not database RLS or an authenticated production boundary. Text content remains sensitive storage even after embedding. Expiry prevents retrieval but does not erase disk/backups. Retention erasure, least-privilege deployment and backup policy remain rollout requirements.

## 8. Verification and actual execution

Commands from repository root:

```powershell
$env:PROJECT28_KNOWLEDGE_TEST_URL_FILE=(Resolve-Path '.local/step17-database-url').Path
.venv/Scripts/python.exe -m pytest tests/rag -q --tb=short
.venv/Scripts/python.exe -m ruff check services/knowledge tests/rag
.venv/Scripts/python.exe -m mypy services/knowledge
$env:HF_HUB_OFFLINE='1'
$env:HF_HUB_DISABLE_TELEMETRY='1'
$env:PYTHONPATH=(Get-Location).Path
.local/step13-asr-venv/Scripts/python.exe docs/implementation/evidence/step17-20261029/evaluate.py
```

Final focused suite: **9 passed in 0.18 seconds**, no skips (earlier successful rerun: 0.29 seconds). Ruff passed; mypy passed four source files. The default pytest-asyncio fixture-scope deprecation warning remains unrelated to STEP_17.

Neural evaluation completed successfully on 2026-10-29 after Docker restart. Assertions covered authorized expected hits, wrong-tenant rejection, restricted supervisor passage exclusion and deletion absence. The archived repeatable evaluation script writes to a fresh timestamped output folder with exclusive file creation and a ten-second connection timeout. The executed original used `step17-20261028`; its numeric result was copied unchanged under `step17-20261029` for this execution. These output-path/timeout changes do not change the evaluation algorithm.

An initial resumed test attempt failed because Docker was stopped; its connection waited too long. Restarted Docker Desktop and the dedicated knowledge container, then reran successfully. Added a ten-second test connection timeout. An evaluation attempt waiting on the stopped database was terminated and rerun successfully. Direct and Xet full-file downloads stalled; validated resumable ranged download completed and the full checkpoint hash matched. No failed attempt is counted as a pass.

Full service-configured regression: **399 passed, 1 warning in 64.83 seconds**, exit 0; no skips. Final focused output: **9 passed in 0.18 seconds**, exit 0. See `evidence/step17-20261029/regression.txt` and `focused.txt`. The regression warning is a Starlette/AnyIO deprecation. Ruff and mypy were rerun successfully after the connection-timeout edit. Exact regression command uses existing ignored admin/application URL files plus the knowledge URL file and runs `tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets tests/rag -q --tb=short`. No HTTP knowledge endpoint or UI was tested because neither was added.

## 9. Analytics and interpretation

Evidence: [neural-pgvector.json](evidence/step17-20261029/neural-pgvector.json).

| Metric | Actual | Conditions / interpretation |
|---|---|---|
| Recall@1 | **1.0 (2/2)** | Expected approved policy ranked first for both questions; tiny synthetic English fixture only |
| Encoding | **2.4646073 seconds** | Three procedure texts plus two queries on CPU; excludes model loading/hash |
| Index insertion | **0.1896453 seconds** | Three single-chunk documents with precomputed vectors; includes transactions, excludes embedding/setup |
| Storage | **204,800 bytes** | Sum pg_total_relation_size of both tables after deletion; includes indexes/TOAST and existing synthetic test rows |
| Embedding dimension | **1024** | Actual neural output checked |
| Production relevance / multilingual accuracy | **Not measured** | No representative company corpus |
| Baseline, p50/p95, throughput, GPU peak | **Not measured** | No prior upstream knowledge index; single smoke run, CPU only |

Recall@1 = queries whose first retrieved document equals the expected document / total queries. This proves a functioning path and these specific assertions; it is not a general accuracy estimate or an improvement over upstream. Storage is total relation allocation, not an incremental per-document benchmark.

## 10. Questions with detailed answers

1. **Why store chunk provenance?** A citation must resolve to a particular procedure version and passage. UUID, version, ordinal and content digest distinguish an updated policy from a stale answer; the full digest supports integrity checks.
2. **Why filter permissions before generation?** A generator cannot safely erase knowledge it already received. SQL excludes unauthorized passages before they leave storage; STEP_18 must preserve that identity boundary.
3. **Why version embeddings?** Coordinates depend on the encoder. Comparing a query encoded by a different revision can silently rank unrelated passages; retrieval explicitly matches the stored revision.
4. **What does the execution prove?** Real BGE vectors were stored and ranked in real pgvector; two expected hits, tenant isolation, role exclusion and deletion assertions passed. It does not prove production corpus recall.
5. **Why exact search instead of HNSW?** Exact cosine search avoids approximate-recall and filtered-index tuning for three documents. Large corpora need measured latency/recall and a migration before selecting an approximate index.
6. **What happens on update failure?** Validation happens before replacement; the SQL transaction rolls back any later failed insertion. An advisory lock serializes cooperating replacements and stale versions are rejected. The active-only design does not preserve historical source text.
7. **Why reject PDF and long token sequences?** A minimal allowlist avoids executing complex document parsers. Refusing oversize token input prevents silent text loss. Supporting more formats or token-aware rechunking needs additional explicit implementation and validation.

## 11. Decisions, risks and remaining limitations

- Chose bounded TXT/Markdown and null pages rather than pretending PDF pagination exists. PDF/DOCX extraction remains unsupported.
- Chose isolated pgvector service and explicit bootstrap instead of changing the application's existing PostgreSQL image/migrations. Production deployment needs a reviewed migration and restricted DB role/RLS.
- Internal Python callers are trusted. Authenticated approval workflows, HTTP routes and an administrative UI are absent; do not expose these functions directly to untrusted identity inputs.
- Active version only. Historical citations cannot resolve after replacement; archival policy is future work.
- Expiry filtering is implemented; automatic retention erasure/backups are not.
- Exact search, CPU-only smoke and two queries do not establish scale, multilingual quality or operational SLOs. No index-build baseline or VRAM result was measured.
- The original seven audio limitations in `CURRENT_LIMITATIONS.md` remain; this knowledge work does not resolve them.

## 12. Actual deliverables, next handoff and evidence checklist

All three STEP_17 prototype done gates passed: authorized documents searchable, forbidden-role chunks excluded and deleted documents unavailable. Decision: **PASS WITH LIMITATIONS** under the trusted internal service scope. STEP_18 is next eligible subject to its own prerequisites. Do not claim public production deployment readiness.

Next safe command: `Get-Content prompts/STEP_18_ground_qa_and_recommendations_in_rag_PROMPT.md`. Do not execute STEP_18 automatically. It must obtain trusted identity, use these filtering contracts, defend against instructions in retrieved content, verify source citations and label missing evidence. Production route integration must address the authentication/deployment gaps above.

- [x] Actual source additions and scoped inventory saved.
- [x] Complete model checksum verified and local inference executed.
- [x] Real database ACL/update/delete tests executed.
- [x] Synthetic-only metrics linked with denominators and limitations.
- [x] Imports, architecture, Q&A, failure history and handoff documented.
- [x] No commit, push, public deployment or production database migration performed.

## 13. Approved ERP UI design / visual contract verification

**Not applicable to visual verification:** this step changes internal Python contracts only; no page, frontend component, HTTP route, CSS or browser interaction changed. Original Gradio behavior is retained. No UI screenshot or accessibility result is claimed. `design/UI_DESIGN_SYSTEM.md` and acceptance checklist were reviewed; the approved Commercially green-and-neutral reference remains mandatory for future UI.

Document source, department, grants, version, expiry, approval, section and citation fields support the future Knowledge Base table and permissions display. There is no ingestion-status endpoint yet; future UI must derive actual states and display validation errors rather than invent progress. Color tokens, responsive layout, keyboard/contrast and screenshots require validation when that UI is built.

### Final repeatability check (2026-10-29)

The archived evaluation script also executed successfully after formatting and adding bounded connection setup: Recall@1 **2/2**, encoding **0.2934736 seconds**, insertion **0.0246019 seconds**, total relation allocation **245760 bytes** (including accumulated synthetic rows). All ACL/deletion assertions passed again. The timing variation between runs is not an optimization claim; initialization/cache/system conditions differ and neither run estimates p95. A new `evidence/step17-repeat-*` folder contains the second raw result. Final Ruff check includes the archived script and passes. The last edit splits a SQL string across two adjacent literals without changing its query.
