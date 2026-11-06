# GPU verification — 2026-10-26

**Latest result: PASS — cached tiny Whisper on CUDA/float16 and a durable GPU job.**

See the correction below. The initial failed verification is retained as history.

## Initial diagnosis

**Initial result: hardware visibility PASS; inference FAIL in the former image.**

The RTX4060 is visible to the host and to the opt-in worker-gpu Compose profile.
CTranslate2 4.8.3 detects one CUDA device and advertises float16 and other compute
types. The existing cached tiny Whisper model loaded with explicit cuda/float16
(no CPU fallback), but actual transcription of a10-second bundled sample failed:

`RuntimeError: Library libcublas.so.12 is not found or cannot be loaded`

Library probes confirm the injected driver libcuda.so.1 is loadable, while
libcublas.so.12, libcublasLt.so.12 and libcudnn.so.9 are absent. GPU enumeration and
model construction alone therefore do not establish working GPU inference.

This was a verification-only request. No packages, image definitions, model files,
credentials or application behavior were changed. Temporary GPU test containers
were removed. Existing CPU services remain the working path. No new inference
latency/accuracy/VRAM-peak claim is made because the GPU transcription did not run.

Next correction: supply the required CUDA runtime libraries in a dedicated GPU
image, then repeat the actual transcription and durable GPU-job checks. Keep CPU
and GPU images separate and preserve explicit device selection. Driver capability
is not evidence that those user-space runtime libraries are installed.

Evidence: `../implementation/evidence/gpu-verification-20261026T150301Z/` contains raw Docker test,
library probes and exact host GPU/driver/VRAM readings. STEP10 remains PASS WITH
LIMITATIONS for its verified CPU scope; its previously unverified GPU limitation
is now a confirmed image-runtime blocker. No next implementation step executed.


## Correction completed — 2026-10-26

A separate `Dockerfile.gpu` / `project28-app:gpu` image now installs pinned Linux
NVIDIA cuBLAS12.9.2.10, cuDNN9.27.0.42 and NVRTC12.9.86. Library directories are
registered with ldconfig. The CPU image and host Python packages are unchanged;
no driver, checkpoint or model size was replaced and no model was downloaded.
The GPU profile uses this image and the worker rejects missing CUDA devices or
required libraries before consuming jobs.

Actual results:

- Explicit cuda/float16, cached tiny Whisper,10-second clip: **0.711s** transcription
  after **0.977s** loading; one English segment. Lazy results were fully consumed.
- Sampled whole-GPU maximum: **267MiB** during that short probe. This is not an
  isolated model peak, guaranteed peak, large-model budget or production benchmark.
- Real durable GPU worker: queued → running → finished, one attempt;
  **7.645s** worker execution and **0.747s** queue wait for the full bundled sample.
  Upload202, report/PDF200, duplicate upload returned the same logical job ID.
- Full regression: **260 passed in42.57s**, including four startup rejection cases;
  Ruff/format/mypy/dependency checks pass. Actual GPU kernels, not mocks, were used
  by the separate hardware checks. CPU image ID comparison confirms it was unchanged.
- The local GPU worker is running; the API still correctly requires a real IdP
  before normal user sign-in. Demo identities were ephemeral signed test fixtures.

Reproduce after building the base application image:

```powershell
docker compose --env-file .env.docker -f compose.local.yml -f infrastructure/compose/queue.local.yml --profile gpu build worker-gpu
docker compose --env-file .env.docker -f compose.local.yml -f infrastructure/compose/queue.local.yml --profile gpu run --rm -T --no-deps worker-gpu python -m scripts.check_gpu_runtime
```

Evidence: `../implementation/evidence/gpu-correction-20261026T150543Z/`. Real IdP integration,
other models/training, GPU load testing and production deployment remain unverified.
No speedup or accuracy improvement is inferred from these single-sample timings.
