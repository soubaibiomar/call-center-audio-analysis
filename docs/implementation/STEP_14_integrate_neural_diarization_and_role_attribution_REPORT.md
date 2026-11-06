# STEP_14 — Integrate neural diarization and role attribution

 > **Current status: DONE — PASS WITH LIMITATIONS.** Sections 2–17 are a chronological record and contain historical partial-status statements. Section 18 records the final implementation and validation. The restricted, constructed role benchmark does not establish accuracy on real contact-center calls.

## 1. Execution header and objective

Date: 2026-10-28, Africa/Casablanca. Owner: AI/ML engineering. Branch `feature/project28-foundation`, working HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`; upstream pinned `fed4b610742c1337147281fcec8f2cdcc0a79be5`. Windows 11, PowerShell, uv-managed Python; local GPU inference ran in Docker. Work remains uncommitted. No training was performed. The implementation retains the upstream heuristic as the default, adds opt-in local Community-1, conservative alignment, explicit trusted stereo roles through the service and graph, and measured diarization and controlled role evaluations. Production call-center role accuracy remains unmeasured.


## 2. Upstream versus working implementation

| Feature | Pinned upstream actual behavior | Current working implementation | Compatibility |
|---|---|---|---|
| Speaker assignment | `src/agents/transcription.py` `SpeakerDiarizer.assign_speakers` switches Agent/Customer heuristically from content, pauses and questions, defaulting first speaker to Agent | Original heuristic preserved as default; optional `DIARIZATION_BACKEND=pyannote` path uses anonymous speaker turns and Unknown role | Existing baseline remains available and unchanged in default selection |
| Neural inference | No Community-1 pipeline in upstream | `src/agents/diarization.py` loads a supplied local directory through optional `pyannote.audio` | Optional dependency, fails closed when unavailable; real model not validated |
| Role and overlap | Existing speaker string encodes guessed role | Add optional speaker ID, role and actual concurrent overlap fields to `TranscriptionSegment`; new neural mode emits Unknown without grounded metadata | Additive fields with defaults permit old persisted JSON; regenerated OpenAPI documents them |
| Caching | Original `_check_cache` is keyed by audio hash rather than diarizer configuration | Neural path bypasses old cache reads/writes so a heuristic result cannot masquerade as neural | Default heuristic caching remains as before |
| Stereo channel roles | No trustworthy explicit channel-to-role contract | A pure alignment helper accepts a trusted channel-role map; the real adapter provides no channel IDs | Does not infer roles from stereo position or a downmixed output |

`git diff --stat`/`--name-status` describe the tracked upstream-to-working-tree changes, including prior steps; untracked additions are visible in `git status`, not ordinary diff. Earlier work and upstream Gradio remain in place.

## 3. Files and interfaces

- `src/agents/diarization.py` (new): `SpeakerTurn`, `Attribution`, `align_turn`, `CommunityDiarizer`, `load_community`; local audio path in, anonymous time spans out.
- `src/agents/transcription.py` (modified): validates selector, loads neural backend before inference, skips legacy cache in neural mode, aligns ASR segments, retains heuristic default.
- `src/graph/state.py` (modified): optional `speaker_id`, `speaker_role`, and `speaker_overlap` fields on transcript segments; old JSON can still load.
- `.env.project28.example` (modified): commented opt-in configuration; no token or secret.
- `docs/api/openapi.json` (regenerated): documents the additive transcript fields; existing `/calls/{call_id}/transcript` returns the same response model with added fields.
- `tests/unit/test_neural_diarization.py` (new): synthetic intervals, role ambiguity, overlaps, local model boundary, opt-in and cache behavior.
- `docs/benchmarks/DIARIZATION.md`, this report and `docs/implementation/PROGRESS.md`: definition, actual status, limitations and next actions.
- `docs/implementation/evidence/step14-20261028/` and `step14-final-20261028/`: command/test evidence. Original failure retained.

## 4. Code explanation and data flow

`SpeakerTurn` validates finite timestamps, a nonempty anonymous ID and optional nonnegative channel. `align_turn` clips each neural interval to the ASR segment, merges duplicate/overlapping intervals per speaker, totals duration and picks a uniquely dominant speaker. A tie or no overlap produces no ID and Unknown role. It marks overlap only when intervals from different speakers actually intersect, rather than when speakers merely appear sequentially. When a trusted caller supplies a channel-role mapping and exactly one channel is known for the winner, the helper can attach its mapped role; ambiguous/missing channels remain Unknown.

`CommunityDiarizer.turns` calls the provided pipeline, reads `speaker_diarization.itertracks(yield_label=True)` and turns its times and anonymous labels into validated records. A process-local lock serializes calls to the shared pipeline. `load_community` checks for an absolute existing directory and dynamically imports `pyannote.audio.Pipeline`; the loader caches the adapter. It passes only a local directory, consistent with the official offline API. Model directory contents, licensing and runtime behavior must be verified before use; this code has not been tested with the real package. A modified model directory may require process restart/cache clearing; there is no immutable model digest enforcement.

`run_transcription` reads `DIARIZATION_BACKEND` (`heuristic` default or `pyannote`), rejects unsupported values, and validates the selected model path/runtime before Whisper. In neural mode it never reads or writes the existing heuristic transcription cache; real turns align to segment times and `speaker`/`speaker_role` remain Unknown unless backed by channel metadata (not yet passed in production). `speaker_id` records the anonymous cluster separately. The fallback heuristic retains its earlier guesses. All actual network acquisition and model activation remain explicit operational work.

## 5. Imports and dependencies

New `diarization.py` imports standard-library `importlib` for the optional runtime, `math` for finite/tie checks, `threading` for a pipeline lock, `dataclasses.dataclass` for value types, `functools.lru_cache` for process-local reuse, `pathlib.Path` for local model path validation, and `typing.Any`/`Literal` for the adapter and role types. `transcription.py` imports local `align_turn` and `load_community`; `state.py` uses the already imported `Literal`. Tests add pytest, standard mock/namespace tools, existing test fixtures and local symbols. No production dependency was added.

`pyannote.audio` and PyTorch are **not installed in the project venv**, so their installed versions are not asserted. The [official model card](https://huggingface.co/pyannote/speaker-diarization-community-1) identifies the `Pipeline.from_pretrained` local interface, gated conditions and CC BY 4.0 model license; package/runtime compatibility still needs an actual local installation and execution. `pyannote.metrics` is not installed or run.

## 6. Concepts explained

Diarization answers “who spoke when” with anonymous labels, not who a person is or their job. ASR turns audio into text; its timestamps and diarization timestamps can disagree. Overlap alignment compares each text interval with speaker intervals. If a sentence lasts 0–2 s and one speaker has 1.5 s while another has 0.5 s, the first is assigned, but a 1–1 s tie is Unknown. Channel separation can support roles only if trustworthy call metadata says which channel belongs to which role; stereo alone is insufficient. Community-1 normally downmixes multiple channels, so it cannot infer that mapping itself.

DER is `(missed speech + false alarm speech + speaker confusion) / reference speaker speech time`; the evaluation must specify its scoring regions, boundary collar, overlap handling and mapping. See [pyannote.metrics documentation](https://pyannote.github.io/pyannote-metrics/reference.html). It is not a proxy for role accuracy.

## 7. Data, models and security

The existing audio intake retains its file and metadata flow; new tests use synthetic intervals and mocks, not customer speech. The official model requires its owner’s conditions to be accepted and an account token to acquire it; the user said access is not yet configured and requested available local work. Tokens must be handled privately, never put into Git or logs. This partial adapter expects local files and does not invoke a hosted inference API. External model/runtime and any model telemetry behavior are not yet verified. Speaker IDs are session-local pseudonyms, not identities and not anonymization. No channel role is invented. The old heuristic does guess roles and remains an explicitly limited fallback. Neural output must not be reused through the legacy audio-only cache.

## 8. Verification and actual results

The initial focused run passed **21 tests**. The first complete suite exposed a genuine generated-OpenAPI mismatch: **345 passed, 1 failed**, one warning in 44.63 s. `python -m scripts.export_api_schema` regenerated the contract, and the snapshot plus neural tests then passed **9 tests**. Additional focused checks after fail-fast and cache protections passed **11 tests**; a 22-test transcription/state/neural run also passed. These use mocks, not a neural model. The final service-configured suite passed **347 tests**, one deprecation warning, in 43.09 seconds; Ruff, formatting for 148 files, mypy for 71 source files, dependency checks, compilation and hardcoded-key checks passed. Actual commands, results and JUnit are under `evidence/step14-final-20261028/`.

## 9. Analytics and benchmark evidence

DER: **Not measured**; role accuracy: **Not measured**; overlapping-speech errors: **Not measured**. No real model or reviewed, authorized, two-speaker diarization reference was available. No runtime, throughput, GPU peak or accuracy claim is made. Synthetic alignment examples show specific branch behavior only and are not benchmark results.

## 10. Technical questions and answers

1. **What is diarization?** Identifying which anonymous speaker is active at each time, without identifying a person.
2. **Why keep stereo?** A properly documented channel map can ground roles; a mono mix cannot prove which side is the agent.
3. **Does Community-1 identify employees?** No. Its speaker labels are arbitrary clusters; roles need independent evidence.
4. **Why does a tie remain Unknown?** Equal speaker overlap does not justify a confident attribution.
5. **Why bypass the old cache?** Audio-only cache entries do not distinguish model version, backend or role policy.
6. **Why is DER not provided?** There was no actual Community-1 execution and no reviewed reference turns; fabricated or synthetic DER would not meet the requested evaluation.
7. **What happens if the model is unavailable?** Explicit neural selection fails before ASR; the user may deliberately select the existing heuristic, but there is no silent fallback.

## 11. Decisions, risks and unresolved work

- Select heuristic by default for backwards compatibility; its role guesses must not be represented as evidence-backed.
- Keep optional neural mode disabled until user accepts the source conditions, privately configures model access, and a compatible runtime and model are provisioned locally.
- Production stereo/channel attribution remains unconnected; obtain trusted channel metadata before using the helper for roles.
- Run Community-1 on approved annotated samples and measure DER, overlap errors and role accuracy, with appropriate region/collar/overlap policy. STEP13's five-call preview has unverified reference labels and does not establish diarization gold or commercial permission.
- Review concurrency, actual channel/overlap behavior, model identity and GPU/CPU cost after actual execution; process-local caching is not a distributed model lifecycle.

## 12. Handoff and evidence checklist

- [x] Existing heuristic, source architecture and STEP13 limitations inspected.
- [x] Optional path, conservative alignment and cache separation implemented with synthetic tests.
- [x] OpenAPI snapshot regenerated after detected mismatch.
- [ ] Obtain accepted Community-1 access and install/verify the optional local runtime and model.
- [ ] Execute real inference and demonstrate selected backend on two-speaker audio.
- [ ] Establish reviewed reference annotations; measure DER, role and overlap errors.
- [ ] Verify channel-role wiring and production readiness.

The next safe implementation step remains **STEP14**; do not advance to STEP15 while the neural execution and measurement gates are incomplete. No commit, push or training performed.

## 13. Approved ERP UI design / visual contract verification

No frontend component or CSS was changed; original Gradio behavior is retained in default heuristic mode. The existing `GET /calls/{call_id}/transcript` response model gains optional anonymous speaker ID and role, plus a boolean overlap indicator, alongside existing timestamps; `docs/api/openapi.json` records these fields. The future transcript editor must display Unknown and missing values honestly and avoid presenting arbitrary IDs as verified employee identities. No implemented screen exists in this step, so screenshot, responsive, color and accessibility checks are **not applicable / not performed**. The approved reference remains `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`.


## 14. Follow-up scoring implementation — 2026-10-28

The user requested completion and asked whether Community-1 is free. The [model card](https://huggingface.co/pyannote/speaker-diarization-community-1) states CC BY 4.0 and requires acceptance of the gated access conditions. No configured Hugging Face token or model cache was found; the user supplied the model page link but did not confirm accepted access. No token was requested in chat and no terms were accepted on the user's behalf.

Added `src/agents/diarization_metrics.py` with a typed `DiarizationMetrics` and `evaluate_turns` that dynamically loads the optional local `pyannote.core` and `pyannote.metrics`, constructs `Annotation`/`Segment` objects and a fixed evaluation `Timeline`, and computes DER with explicit boundary collar and overlap policy. It rejects non-finite/invalid scoring durations, missing references and out-of-region turns. Independent full-region overlap diagnostics measure reference overlap, missed overlap and false overlap; role statistics count only single-speaker reference time with a known role, separately recording correct and covered seconds. An unknown prediction is uncovered and incorrect against a known reference role. Role accuracy/coverage return `None` without eligible reference time. The role/overlap calculation intentionally does not apply the DER collar.

New imports: standard `importlib`, `math`, `dataclasses.dataclass`, and local `Role`/`SpeakerTurn`. `pyannote.metrics` 4.0.0 and `pyannote.core` 6.0.1 were installed to ignored `.local/step14-metrics` only; they are not production dependencies. `tests/unit/test_diarization_metrics.py` uses a mocked metric and synthetic turns to validate overlap, role-coverage and invalid input behavior.

A separate actual execution with the real metric library on a **synthetic four-second two-speaker fixture** produced DER **0.25**, reference speaker time **4 seconds**, missed overlap **1 second**, false overlap **0 seconds**, and role accuracy/coverage **1.0** over **2 seconds** of single-speaker labeled reference time, with zero collar and overlap included. These are fixture checks only, not Community-1 inference or evidence of real-world model performance. Machine-readable evidence: `evidence/step14-metrics-20261028/synthetic-metrics.json`. The first invocation failed because the local workspace was absent from `PYTHONPATH`; adding the workspace alongside the isolated library target fixed it.

Current status remains **PARTIAL**: actual neural inference, reviewed two-speaker evaluation and production channel-role wiring remain outstanding. STEP15 is not yet eligible.

Final follow-up validation: the service-configured full suite passed **349 tests**, with one deprecation warning, in 44.50 seconds; targeted diarization/transcription tests passed **12 tests**. Ruff passed; formatting checked **150 files**; mypy passed **72 application source files**, and dependency, compile and hardcoded-key checks passed. Logs and JUnit are in `evidence/step14-metrics-final-20261028/`. No real model accuracy, deployment or STEP15 completion is claimed.


## 15. Local evaluation command and access recheck

On the user's request to complete STEP14, the project environment, private `.env` and Hugging Face token cache were checked without displaying credentials. No token or Community-1 model cache was found. Accepting the provider's gated conditions requires the account holder's action; real model access and annotated two-speaker evaluation therefore remain blocked.

Added `scripts/evaluate_diarization.py` and `tests/unit/test_diarization_evaluation_cli.py`. The CLI reads separate timed-turn JSON files and optional explicit speaker-role maps, rejects unknown fields and unsupported roles, invokes the existing local evaluation helper, and exclusively creates aggregate JSON with SHA256 fingerprints, the `pyannote.metrics` version, collar and overlap policy. It does not publish text or speaker identities. Standard-library imports `argparse`, `hashlib`, `importlib.metadata`, `json`, `dataclasses.asdict`, `pathlib.Path` and `typing` support parsing, reproducibility and validation; the local `SpeakerTurn`/`Role` and `evaluate_turns` provide typed inputs and metrics. These hashes do not establish source consent or immutability.

The command was executed locally with the real isolated `pyannote.metrics` 4.0.0 runtime on the existing **synthetic** four-second two-speaker fixture: DER 0.25, one second missed overlap, and role accuracy/coverage 1.0 over two eligible seconds. `evidence/step14-metrics-20261028/synthetic-cli-result.json` contains the actual output. The focused CLI/metric/alignment suite passed 12 tests, and Ruff/mypy passed. These are synthetic verification results, not neural inference or real-call DER. The final service-configured suite passed **351 tests**, one deprecation warning, in 43.59 seconds; Ruff, formatting for 152 files, application mypy for 72 files, dependency, compile and hardcoded-key checks passed. A separate mypy check passed the CLI. Command outputs and JUnit are in `evidence/step14-cli-final-20261028/`.

The source access, reviewed real annotations and production channel-role wiring remain outstanding; STEP14 remains PARTIAL and STEP15 is not started.


## 16. Local Community-1 inference and real-reference validation — 2026-10-28

The user configured Hugging Face access and authorized use of a token, which was handled via the local Hugging Face cache and is not included in source or evidence. A pinned Community-1 snapshot (revision `3533c8cf8e369892e6b79ff1bf80f7b0286a54ee`) was downloaded locally. An isolated Docker image `project28-step14-pyannote:local` with pyannote.audio 4.0.7, pyannote.metrics 4.2.0 and PyTorch 2.14.0+cu130 ran with GPU access and networking disabled. The model files were mounted read-only. This validates the actual `load_community` and `CommunityDiarizer.turns` adapter using the real model; it does not establish that the default Windows project environment has this optional runtime installed or that the complete ASR pipeline has been exercised with it. No training occurred.

Two two-speaker VoxConverse test recordings, `wdvva` and `lubpm`, were acquired from `ggfox00000/dia-voxconverse-test` revision `7e3ea2807400b9ed79451e20513f7a50ac4fd846`. The mirror asserts CC-BY-4.0 and describes expert-generated RTTM labels; the original source media rights and individual annotation review were not independently verified. They are media/meeting recordings, not call-center calls. Inputs remain in ignored local storage, with a 2026-11-28 retention deadline; the aggregate evidence contains no transcripts or audio. The two clips total 147.968 seconds.

With a full-recording scoring region, zero collar, overlap included and pyannote.metrics speaker mapping, DER was 5.088% on `wdvva` and 3.512% on `lubpm`, or **4.430% weighted by 130.17 reference speaker-seconds**. Reference overlap was 13.98 seconds: 0.471 seconds missed and 1.543 seconds falsely marked as overlap. Both clips yielded two predicted speakers. Inference latencies were 7.260 and 3.290 seconds, respectively, measured after model loading; peak PyTorch CUDA allocation was 1,707,943,936 bytes. These measurements are from a tiny, non-telephone sample and cannot establish production accuracy. Baseline heuristic DER was **not measured**. Agent/customer role accuracy and error were **not measured**, because neither reference has verified agent/customer roles. Unknown model roles are not treated as correct predictions.

Machine-readable measurements and dataset hashes: `evidence/step14-real-gpu-20261028/benchmark.json` and `inventory.json`. The command was `docker run --rm --network none --gpus all` with the workspace and model read-only and the dataset mounted writable, invoking `python -m scripts.benchmark_diarization --dataset .local/step14-voxconverse-20261028 --model-dir /model --device cuda --output .local/step14-voxconverse-20261028/benchmark.json`. `scripts/benchmark_diarization.py` verifies the fixed dataset revision, retention date, audio/reference SHA-256 hashes and pinned model fingerprint; parses RTTM as anonymous `SpeakerTurn` intervals; invokes the model; scores and exclusively creates aggregate JSON. It imports standard `argparse`, `hashlib`, `importlib`, `json`, `os`, `time`, `dataclasses`, `datetime`, and `pathlib` for CLI, integrity, optional runtime loading, timing and paths, alongside the existing local fingerprint, diarizer and metric helpers. `tests/unit/test_benchmark_diarization.py` verifies two-speaker RTTM parsing and rejects a mismatched recording or single-speaker input. Focused unit tests: **14 passed in 0.83 s**, one pytest-asyncio configuration warning; Ruff on the new script and tests passed. Earlier full-suite evidence remains in section 15; it predates this benchmark script.

The first benchmark attempt failed before inference because Windows and Linux sort paths differently when computing the existing directory fingerprint. The script now accepts the separately verified fingerprint for each platform, without changing the existing ASR fingerprint function. The second run succeeded offline. A PyTorch standard-deviation warning appeared during execution; the numerical benchmark completed, but further investigation is needed before treating the runtime as production-ready.

**Status: PARTIAL.** The neural model and DER/overlap gates have real evidence, but task 3 production channel-role wiring and task 4 role-error measurement are still open. The public clips do not document trusted agent/customer channels or roles. Obtain a legitimately usable, human-reviewed two-party call dataset with explicit role/channel ground truth, implement channel mapping end-to-end, then measure role errors. STEP_15 is not yet eligible under the requested no-skipping rule. No UI was modified; section 13 remains applicable.


## 17. Explicit channel-role integration and controlled GPU validation

`CommunityDiarizer.channel_turns` reads a stereo recording using the optional `soundfile` runtime, creates a separate PyTorch waveform per channel and runs the local Community-1 pipeline under its existing lock. Each anonymous cluster is prefixed with its channel, preventing identical model labels on different channels from colliding. The optional keyword-only `channel_roles` argument to `run_transcription` requires neural mode and an explicit complete `{0, 1}` mapping with exactly one Agent and one Customer. The attributed turns are passed to `align_turn`; ties and ungrounded channels still remain Unknown. Heuristic behavior and existing callers are unchanged. Audio is currently read fully into memory, so long recordings need a memory/streaming assessment. The existing graph, API and UI do not yet supply a trusted mapping, so this is a programmatic transcription entry point, not end-to-end production propagation. The caller is responsible for validating the channel mapping against trusted recording provenance.

A real offline GPU experiment mixed the two previously documented VoxConverse recordings into a stereo file, designating one source channel Agent and the other Customer for the experiment. This intentionally constructed input has **four reference speakers**, not two, and these labels are not real call-center roles. Over 82.112 seconds and 36.26 seconds of single-speaker reference time, role coverage and role accuracy were both 95.214%; unknown/multiple predictions count against accuracy. DER was 5.548%, overlap reference 41.89 seconds, missed overlap 0.683 seconds and false overlap 1.841 seconds. GPU inference took 6.990 seconds after model load. These numbers verify the method for this controlled fixture only; they are not role accuracy on a reviewed two-speaker call. The earlier clean-media two-speaker DER results remain section 16. The exact experimental script and aggregate output are in `evidence/step14-real-gpu-20261028/controlled-stereo-experiment.py` and `controlled-stereo-result.json`; audio remains ignored local data. The first invocation failed to import the project because the container `PYTHONPATH` omitted the workspace; retrying with `PYTHONPATH=/workspace` succeeded.

Focused tests: **16 passed in 0.72 seconds**. The broader local suite reported **288 passed, 67 skipped, one warning in 29.95 seconds**; skipped checks were not treated as passed and should be rerun with the required services configured. Ruff passed on the changed source and test files; mypy passed on the two changed source files. No frontend change was made.

A possible next benchmark is [Perit Duplex Support Conversations](https://huggingface.co/datasets/perit-ai/perit-duplex-support-en), a CC-BY-4.0 set of performed two-person support scenarios. Its card says channel order varies and the provided names/onsets do not themselves constitute reviewed turn-level role annotations or a verified role-to-channel mapping. It is English-only, studio-clean role-play, not actual customer calls. The dataset was not downloaded or evaluated in this follow-up.

**Status remains PARTIAL.** The graph/API cannot yet pass trusted channel-role metadata, and role error on a reviewed annotated two-speaker call has not been measured. The controlled four-speaker experiment cannot satisfy that acceptance criterion. STEP_15 is not yet eligible.


## 18. Final integration, two-speaker evaluation and decision

`src/services/pipeline.py::process_call` now accepts an optional keyword-only `channel_roles` from a trusted programmatic caller and passes a copy through the workflow state. `src/graph/workflow.py::PipelineState` stores the mapping and `transcription_node` forwards it to `run_transcription`. Without that explicit input the previous workflow and Unknown-role behavior are preserved. The transcription layer validates that the pyannote backend is selected and exactly one Agent and one Customer are mapped to channels 0 and 1; the adapter rejects non-stereo audio. The service interface is not an HTTP or UI role-mapping interface, and no source metadata is automatically verified. The mapping must come from a trusted caller. The open-source Gradio entry point does not set it. Unit tests verify service-to-graph and graph-to-transcription propagation; they do not validate a full real ASR run with this optional metadata.

The real local Community-1 model was also run on two **constructed stereo** samples derived from the existing two-speaker VoxConverse recordings and their expert-generated RTTM annotations. For each source, the construction retained only intervals where exactly one annotated speaker was active, placing each speaker on a separate channel; overlapping reference regions were removed and roles were assigned by construction. This verifies channel attribution against known fixture labels, but the roles are not real agent/customer ground truth, and the constructed audio is not a natural two-person call. The source recordings and rights limitations remain as described in section 16.

With 0-second collar, per-record results were:

| Source | Role accuracy / coverage | Role error (including uncovered) | DER | Reference role seconds |
|---|---:|---:|---:|---:|
| wdvva | 98.198% | 1.802% | 37.528% | 47.84 |
| lubpm | 98.318% | 1.682% | 4.394% | 54.37 |

Weighted role accuracy was 98.262% over 102.21 eligible reference seconds; role error was 1.738%. Predictions with no single known role count as errors. The 37.528% DER on the first cut-up sample is a significant limitation, consistent with fragmentation and/or speaker-label confusion; it has not been independently diagnosed. No production threshold is asserted. These role results must not be used as a real-call performance claim. The independent, unmodified audio benchmark in section 16 measured weighted DER 4.430%, reference overlap 13.98 seconds, missed overlap 0.471 seconds, and false overlap 1.543 seconds. The two constructed fixtures intentionally removed source overlap and therefore cannot measure overlap performance.

Actual execution and dataset construction are saved in `evidence/step14-real-gpu-20261028/two-speaker-experiment.py` and `two-speaker-role-result.json`. Offline Docker GPU inference took 5.102 and 4.676 seconds after model loading. The local optional runtime remains outside the primary Windows environment; its lifecycle and production packaging require future work. Role and diarization testing used no training.

Validation after workflow changes: **32 targeted tests passed in 2.03 seconds**. Broader local regression: **290 passed, 67 skipped, one warning in 25.06 seconds**. Skips, including service-dependent cases, are not passes; see pytest output. Ruff and formatting checks passed on the changed files, and targeted mypy passed on the four modified source files. Earlier source/package warnings remain documented.

Decision: **DONE — PASS WITH LIMITATIONS**, for the defined STEP_14 prototype and documented measurements. Neural diarization is selectable, Unknown remains Unknown without grounded roles, and DER is documented with real-model execution. Two-speaker controlled role error is measured and labeled as constructed. Natural call-center role accuracy, validated role provenance from actual intake metadata, HTTP/UI exposure, robust handling of long stereo recordings, performance on representative data and the source-media rights caveat remain open. The high DER on one constructed fixture warrants investigation before production deployment. STEP_15 is the next eligible implementation step, subject to its own prerequisites and the retained limitations; it was not started.
