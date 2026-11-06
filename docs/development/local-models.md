# Local Qwen inference — STEP11

The existing OpenAI/Gemini/Groq selection is preserved. Local inference is opt-in:

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:OLLAMA_MODEL = 'qwen2.5-coder:7b'
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434/v1'
$env:LLM_TIMEOUT_SECONDS = '120'
```

Use private `.env` for persistent settings, then restart only project app/workers.
Inside Docker use `http://host.docker.internal:11434/v1` (or the Ollama service name
if deliberately attached to the same private network). No hosted API key is needed
for this provider. The adapter supplies the SDK's dummy local key, disables proxies
and redirects, uses temperature0/2048 output tokens and SDK retries0. The agent owns
a 1–5 attempt budget with bounded exponential waits. Each request has its configured
read timeout; this is not a whole-job deadline or cancellation of server inference.
`reasoning_effort=none` controls thinking on the tested OpenAI-compatible endpoint.
No automatic cloud/model fallback, model pull, daemon restart or configuration edit
occurs. Invalid provider names fail explicitly rather than silently choosing OpenAI.

Cached-model tags only: verify `docker exec ollama ollama list`. The selected model
is requested by its exact tag; a missing model is a safe provider_http_error. Endpoint
hosts are restricted to localhost,127.0.0.1,::1,ollama,host.docker.internal and the
credential-free HTTP `/v1` path. This is trusted local development, not authenticated
remote serving. Do not expose Ollama on a public interface or add arbitrary remote
hosts to bypass the policy. Inference still needs the graph's PII/injection checks.
Keep tracing off for sensitive calls: inherited third-party tracing/private logs are
not made safe merely by the new content-free receipts.

Summary and QA use the same original Pydantic schemas. JSON Schema generation guides
the local response; Pydantic validates it again. Schema validity does not establish
factual accuracy or grounding. QA's original weights and trusted call UUID overwrite
remain. Completed report JSON and authorized API `Report.model_runs` expose model
ID/configured version tag, prompt hash revision, schema, attempt/retries, latency,
validity, safe error code and explicit fallback=none. Legacy reports decode with an
empty list. Terminal failures keep safe content-free receipts in logs and graph
state; no completed report is invented. Job status continues exposing its existing
sanitized error_code. There is no new Model Lab UI/endpoint or identity bypass.

ModelRun.model_version is the configured tag, not an immutable registry digest.
Benchmark receipts additionally record Ollama's actual digest. Pin/manage mutable
model tags before regulated/reproducible deployment. No new model registry is added.

## Reproduce the synthetic comparison

```powershell
.venv/Scripts/python.exe -m scripts.benchmark_local_llm --output .local/new-qwen-benchmark
```

The output directory must not exist. It compares the already cached 7B code-tuned
Qwen and 9B Qwen using three synthetic English fixtures, summary plus QA each,
serially, one attempt, no audio/ASR/training/downloads. It writes per-case receipts,
response hashes, nearest-rank p95, JSON schema validity and sampled whole-device
VRAM. NVidia sampling can miss short peaks and includes all processes. Ollama `/api/ps`
adds actual resident model memory/context; CPU offload and different default contexts
confound direct GPU-memory comparisons. The server's context settings are preserved.
Keep GPU-heavy work serialized and do not infer concurrent ASR+LLM capacity from it.

2026-10-27 final observations: both models6/6 schema-valid. 7B mixed cold/warm p95
12.383s; 9B33.146s. Sampled device maxima6326/6324MiB respectively. 7B context32768;
9B65536 with CPU/GPU split. These are small-sample contract observations, not an
accuracy benchmark or production latency SLA. The first 9B attempt timed out at120s
before the corrected thinking-control run; historical partial receipts are retained.
No claim of neural learning, WER improvement or superior summary quality is made.

Tests: `python -m pytest tests/llm tests/api/test_model_runs.py -q` with the private
isolated PostgreSQL fixture configuration described in background-jobs.md. Test
identities are synthetic; the external API remains closed without a real IdP.


## STEP11 correction audit — 2026-10-27

A loopback endpoint alone does not establish local inference: Ollama can route a
model alias to a remote/cloud backend. Before constructing each local chat client,
this adapter sends only the model identifier to `/api/show`, with proxies/redirects
disabled and timeout min(request_timeout,10s). It requires nonempty model_info,
details.format=gguf and no remote_model/remote_host marker. Unverifiable or remote
metadata blocks inference with safe local_model_required; inspection network/status
failures remain safe unavailable/timeout/provider_http_error. No transcript is sent
in the metadata request. Models are never pulled or reconfigured by this check.

This trusts the administrator-controlled local daemon and its truthful metadata;
it does not defend against a malicious daemon or an administrator changing an alias
between inspection and inference. Non-GGUF local backends are intentionally rejected
until explicitly supported and validated. This adds a metadata round trip and may
reject a proxy implementing only OpenAI routes; a real local Ollama metadata API is
now required for the privacy contract.

The synchronous validated agent runner closes its owned local HTTP transport on
success or failure using ExitStack. Direct factory consumers remain responsible
for their own client lifecycle; this helper does not implement async inference.
Failure receipts use the same provider/model/environment selection rule as the
factory. Rejected free-form model settings are represented as unresolved so they
are not echoed into receipts. Valid configured identifiers remain visible.

The benchmark writes all observations/results and exits1 if any output fails its
schema/operation, so a failed experiment cannot look green from process status.
Successful runs exit0. Partial receipts remain available after a failure. Exit
status is a contract-validity gate, not a model-quality approval decision.

Latest audit:301 tests pass; eight new regression cases. Both cached Qwen variants
still6/6 schema-valid; sampled whole-device maxima6138/6328MiB, observed p95
8.200s/33.446s. Different warm/loading/offload conditions prevent attributing a
speedup to these corrections. See the STEP11 A–O appendix and correction evidence.
