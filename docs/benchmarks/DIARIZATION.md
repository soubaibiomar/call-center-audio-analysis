# Diarization — STEP14

Status: **STEP_14 prototype complete with limitations**; historical notes below are followed by measured results. Existing heuristic labeling remains the default. Set `DIARIZATION_BACKEND=pyannote` and `DIARIZATION_MODEL_PATH` to an absolute local Community-1 model directory only after installing a compatible `pyannote.audio` runtime and obtaining accepted model terms and access. The optional runtime/model are not bundled or downloaded by the application. An unavailable or invalid explicit neural backend fails; it does not silently fabricate a heuristic result. Neural mode bypasses the original transcription cache because its key does not contain backend or model identity.

Community-1 provides anonymous speaker turns, not a person's identity or agent/customer role. The adapter retains speaker IDs and checks ASR-segment temporal overlap; ties/no evidence return Unknown. Multiple speakers can occur sequentially within an ASR segment, so an overlap flag requires actual simultaneous speaker intervals. The separate channel-role mapping helper only uses a role when trusted metadata explicitly maps the single observed channel; the current Community-1 adapter downmixes and does not supply channel identities, so its roles remain Unknown. Stereo channel role mapping is not wired to production input. Existing heuristic output is retained for compatibility and its Agent/Customer labels are guesses, not proven roles.

**Historical status before the real-model run:** DER, role accuracy and overlap errors were not measured. See the real-reference results below. DER = (missed speech + false-alarm speech + speaker confusion) / reference speaker speech time, with the evaluation region, collar, overlapping-speaker policy and speaker mapping documented. `pyannote.metrics` [reference](https://pyannote.github.io/pyannote-metrics/reference.html) explains those parameters; synthetic alignment unit tests are not DER evidence. Before deployment, run a pinned, local model on authorized, human-reviewed two-speaker reference audio; record model version, duration, overlap/collar settings, DER, role accuracy, overlap errors, latency and peak VRAM. Obtain user approval before any large download.

The source model [Community-1](https://huggingface.co/pyannote/speaker-diarization-community-1) declares CC BY 4.0 and requires accepting conditions before downloading; do not place tokens in source or logs. Respect local audio retention and keep model telemetry/network behavior under review. Model outputs are private derived data.

## Evaluation helper (synthetic validation only)

`src/agents/diarization_metrics.py` provides `evaluate_turns` with an optional local `pyannote.metrics` installation. It creates a fixed 0–duration evaluation region and reports DER with explicit collar and overlap options. Separately it reports full-region overlap missed/false-alarm seconds and role-reference, covered and correct seconds; unknown predictions reduce role coverage and count as incorrect against a known single-speaker reference role. Role accuracy is correct/reference time and is `None` without eligible reference time. Role/overlap summaries deliberately use the full region and do not apply the DER collar. Source-role mappings must be reviewed, not inferred from arbitrary speaker IDs.

Executed synthetic fixture only: pyannote.metrics 4.0.0 and pyannote.core 6.0.1 in an isolated local target; reference has one second of two-speaker overlap that the synthetic hypothesis misses. With 0-second collar and overlap included, DER was 0.25 (1 error speaker-second / 4 reference speaker-seconds); overlap missed 1.0 second and synthetic role accuracy and coverage were 1.0 on two single-speaker reference seconds. This verifies the scoring pipeline for that fixture, **not** model quality or a real-data benchmark. Evidence is `docs/implementation/evidence/step14-metrics-20261028/synthetic-metrics.json`.

## Local evaluation command

`scripts/evaluate_diarization.py` accepts separate local JSON annotations containing `turns` (`start`, `end`, `speaker_id`) and optional trusted `roles` maps. Supply an explicit duration, optional DER collar and overlap policy, and a new output path. For the synthetic fixture executed here:

```powershell
$env:PYTHONPATH="$(Resolve-Path .local/step14-metrics);$(Get-Location)"
.local/step13-asr-venv/Scripts/python.exe -m scripts.evaluate_diarization --reference .local/step14-evaluation-example/reference.json --hypothesis .local/step14-evaluation-example/hypothesis.json --duration 4 --output <new-output.json>
```

The output records annotation hashes, the metrics-library version, scoring policy and aggregate values, but no speaker IDs or transcript text. Do not treat hashes as an authorization or immutability mechanism. The command does not produce annotations or establish that a reference was reviewed.


## Real local GPU run — 2026-10-28

Offline Community-1 inference on two VoxConverse media recordings (147.968 seconds total) produced DER 5.088% and 3.512%, respectively, with zero collar and overlap included; weighted DER was 4.430% over 130.17 reference speaker-seconds. Reference overlap: 13.98 seconds; overlap missed: 0.471 seconds; false overlap: 1.543 seconds. Peak PyTorch GPU allocation was 1,707,943,936 bytes. Two clips are insufficient for generalization, especially to calls. Baseline DER and role accuracy/error were not measured. The mirror claims CC-BY-4.0 and expert-generated annotations; underlying media rights and independent human review were not verified. See `docs/implementation/evidence/step14-real-gpu-20261028/` and STEP_14 report section 16 for source, model revision, runtime, timings and limitations.


## Controlled channel-role experiment

A separately constructed stereo mixture of the two annotated media recordings gave each channel an experimental role. It contained four reference speakers and was not a real two-person call. The real GPU model plus channel attribution produced 95.214% role accuracy and coverage on 36.26 seconds of single-speaker reference time, DER 5.548%, 0.683 seconds missed overlap and 1.841 seconds false overlap. These are method-check measurements, not call-center role accuracy. See STEP_14 report section 17 and its evidence for the setup and remaining gaps.


## Two-speaker controlled role fixtures

Two stereo fixtures were constructed from annotated VoxConverse recordings by retaining non-overlapping speech and assigning each annotated speaker to one experimental role. Weighted role accuracy was 98.262% over 102.21 reference seconds; role error including uncovered predictions was 1.738%. DER on the two cut-up fixtures was 37.528% and 4.394%, respectively. These are constructed role labels, not reviewed agent/customer call roles. Original source overlap was removed from these fixtures. See STEP_14 report section 18 and `docs/implementation/evidence/step14-real-gpu-20261028/` for methods and actual outputs.
