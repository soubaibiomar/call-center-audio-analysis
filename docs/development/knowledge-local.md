# Local STEP_17 knowledge service

The service currently exposes trusted Python interfaces, not an HTTP upload endpoint. Only a trusted ingestion administrator should construct an approved `Document` or provide tenant/department/role identities. Never copy authorization values directly from user-controlled query parameters.

Approved formats: UTF-8 `.txt` and `.md`, up to 2 MiB. Documents require explicit approval, timezone-aware expiry, tenant, department, role grants, source identity and increasing version. Chunk citations include document ID, version, ordinal and content digest. The service records page as null for text formats; it does not invent page numbers.

`BgeM3` requires an absolute local model path, a pinned revision and a runtime with torch and transformers. It uses local-files-only loading, disables remote model code and requests weights-only checkpoint loading. Dense vectors are normalized CLS embeddings with 1024 dimensions. Batches are capped at 16 and chunks over 512 tokens fail rather than silently truncate.

`KnowledgeStore.initialize` is explicit administrative bootstrap against a database that supports pgvector. It creates its extension and tables; it does not change the main application database or run automatically at import. The current test database is a dedicated `project28-knowledge-test` container on loopback port 5547. Its credentials remain under ignored `.local/`. Do not use the application database for these tests.

`replace` atomically replaces active chunks and rejects stale versions under an advisory transaction lock. It retains the latest version only; historical citations require a future archival policy. `search` filters tenant, department, role, expiry, approval and embedding revision in SQL before returning any chunk. It uses exact pgvector cosine ordering rather than an approximate index. `delete` uses tenant and document IDs and cascades to chunks. Callers must commit deletion when using non-autocommit connections. Expired rows are filtered, not automatically erased from storage.

The database account is privileged in this isolated development fixture. Production rollout still needs Alembic integration, a least-privilege role/RLS review, authenticated approval workflows, API routes and retention erasure jobs. Nothing in the service trusts uploaded content as instructions. STEP_18 must apply prompt-injection defenses and citation checks before generation.

Test command, from the repository root:

```powershell
$env:PROJECT28_KNOWLEDGE_TEST_URL_FILE=(Resolve-Path '.local/step17-database-url').Path
.venv/Scripts/python.exe -m pytest tests/rag -q
```

## STEP_18 integration

Bind a trusted server-side scope with `GroundedPolicyService.from_store(store, encoder.encode, revision=revision, tenant_id=tenant, department=department, role=role)` and supply it as `compile_workflow(config, knowledge=service)`. The graph queries after redaction and attaches extractive policy evidence to QA and final reports. No configured service means explicit abstention. Documents need trusted `effective_at` metadata; older undated records abstain. Multiple retrieved passages abstain conservatively. Exact quotation is not semantic compliance verification; scores retain baseline rubric semantics. Source text never enters LLM prompts or tool dispatch in this integration. Public authentication, production wiring and representative recall remain deployment work.
