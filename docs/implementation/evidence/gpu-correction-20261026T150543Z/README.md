# GPU runtime correction — 2026-10-26

The preceding GPU-verification evidence remains unchanged (initial missing-library failure).

- build.json/build-final.json: separate GPU image build, pinned NVIDIA runtime only.
- gpu-transcription.json: actual cached tiny Whisper CUDA/float16 kernels,10s clip;
  full lazy results consumed. Whole-GPU samples are not an isolated/guaranteed peak.
- gpu-worker-http.json: actual durable GPU worker, signed fixture identity, real
  cached ASR/configured hosted provider,202/finished/report/PDF200 and stable duplicate ID.
- tests.json/tests.xml:260 passed including four new startup rejection tests;
  remaining Ruff/format/mypy/dependencies/compile/hardcoded-keys and hooks JSON pass.
- operational.json: all required libraries load, GPU worker running without restart,
  GPU-image dependency compatibility, CPU image unchanged and primary4 reports preserved.
- cpu-image-before.txt: CPU image identity before GPU build.
- gpu-worker-start.json: normal local GPU worker startup; GPU remains profile opt-in.
- source-manifest.json: final relevant source/doc hashes; git files describe accumulated
  uncommitted work. No source history rewrite, commit, push or next implementation step.

Private logs, tokens, test helper config and SQL credentials stay under ignored .local/.
No model/checkpoint or host-driver change. One-off verification containers were
removed; normal GPU and CPU workers remain available. The tested workload is tiny
Whisper; other models/training/sustained load/real IdP deployment are not inferred.
