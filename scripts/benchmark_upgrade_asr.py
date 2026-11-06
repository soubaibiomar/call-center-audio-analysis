"""Local, matched-input ASR benchmark; never changes production routing.

Inputs: existing permission-reviewed AppTek roleplay subset, pinned manifest.
Every backend receives the same mono/16kHz, non-overlapping 30-second chunks.
References are ordered by (start,end); overlap and punctuation affect WER.
"""

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import subprocess
import threading
import time
import unicodedata
from datetime import date
from pathlib import Path


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def normalize_comparison(text):
    """NFKC/casefold; punctuation as boundaries; remove Arabic marks/tatweel.

    Preserve French accents, Arabic letters/hamza and digits. Never translate
    Darija into MSA or equate different lexical forms to improve the score.
    """
    output = []
    for char in unicodedata.normalize("NFKC", text).casefold():
        if (
            char == "\u0640"
            or "\u0610" <= char <= "\u061a"
            or "\u064b" <= char <= "\u065f"
            or char == "\u0670"
            or "\u06d6" <= char <= "\u06ed"
        ):
            continue
        output.append(" " if unicodedata.category(char)[0] in "PS" else char)
    return " ".join("".join(output).split())


def validate_multilingual_manifest(manifest, root):
    if (
        manifest.get("schema_version") != "multilingual-asr-v1"
        or manifest.get("purpose")
        != "local non-commercial evaluation only; no training; no redistribution"
    ):
        raise ValueError("Unapproved manifest purpose/schema")
    if date.fromisoformat(manifest["retention_until"]) < date.today():
        raise ValueError("Benchmark retention expired")
    expected = {
        "fr": ("fsicoli/common_voice_22_0", "CC0-1.0"),
        "ar": ("google/fleurs", "CC-BY-4.0"),
        "ary": ("UBC-NLP/Casablanca", "CC-BY-NC-ND-4.0"),
    }
    for language, (repo, license_id) in expected.items():
        source = manifest["sources"][language]
        if source["repo"] != repo or source["license"] != license_id:
            raise ValueError("Unreviewed source or license")
    seen = set()
    for row in manifest["records"]:
        path = (root / row["filename"]).resolve()
        if not path.is_relative_to(root.resolve()) or row["language"] not in expected:
            raise ValueError("Audio path escapes corpus or invalid language")
        if row["sample_id"] in seen or not normalize_comparison(row["reference"]):
            raise ValueError("Duplicate ID or empty reference")
        if hashlib.sha256(row["reference"].encode()).hexdigest() != row["reference_sha256"]:
            raise ValueError("Reference changed")
        seen.add(row["sample_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["whisper", "qwen", "parakeet"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--languages", nargs="+", choices=["fr", "ar", "ary"])
    parser.add_argument("--qwen-dtype", choices=["float16", "bfloat16"], default="float16")
    parser.add_argument("--private-predictions", type=Path)
    parser.add_argument("--whisper-greedy", action="store_true")
    args = parser.parse_args()
    runner_source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.output.exists() or not 1 <= args.repetitions <= 5:
        raise ValueError("New output and 1..5 repetitions required")
    if args.private_predictions:
        private_path = args.private_predictions.resolve()
        if (
            not args.manifest
            or not private_path.is_relative_to((Path.cwd() / ".local").resolve())
            or private_path.exists()
        ):
            raise ValueError("Private predictions require a manifest and new ignored local path")
    os.environ["HF_HUB_OFFLINE"] = "1"
    import numpy as np
    import soundfile as sf
    from rapidfuzz.distance.Levenshtein import distance
    from scipy.signal import resample_poly

    data = args.manifest.parent if args.manifest else Path(".local/step15-apptek")
    raw = (args.manifest or data / "manifest.json").read_bytes()
    manifest = json.loads(raw)
    if args.manifest:
        if hashlib.sha256(raw).hexdigest() != args.manifest_sha256:
            raise ValueError("Manifest hash changed")
        validate_multilingual_manifest(manifest, data)
        manifest.update(
            repo="multilingual-public-pilot",
            revision=args.manifest_sha256,
            license="per-language source licenses",
        )
    elif (
        manifest["revision"] != "b98967d9946f7f59f58d08624a2a00fe98fe0219"
        or manifest["license"] != "CC-BY-SA-4.0"
    ):
        raise ValueError("Unapproved dataset revision/license")
    samples = []
    for record in manifest["records"]:
        language = record.get("language", "en")
        if args.languages and language not in args.languages:
            continue
        if args.backend == "parakeet" and language in ("ar", "ary"):
            raise ValueError("Parakeet does not list Arabic support; select French only")
        path = data / record["filename"] if args.manifest else data / (record["accent"] + ".wav")
        expected_sha = record["audio_sha256"] if args.manifest else record["sha256"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise ValueError("Audio checksum mismatch")
        audio, rate = sf.read(str(path), dtype="float32")
        if audio.ndim == 2:
            audio = audio.mean(axis=1)
        if rate != 16000:
            factor = math.gcd(rate, 16000)
            audio = resample_poly(audio, 16000 // factor, rate // factor)
        reference = (
            normalize(record["reference"])
            if args.manifest
            else normalize(
                " ".join(
                    segment["text"]
                    for segment in sorted(record["segments"], key=lambda s: (s["start"], s["end"]))
                )
            )
        )
        samples.append((record.get("sample_id", record.get("accent")), audio, reference, language))
    if not samples:
        raise ValueError("No eligible benchmark samples")
    torch = None
    memory = []
    stop = threading.Event()
    if args.device == "cuda":
        if args.backend == "whisper":
            import ctranslate2

            if ctranslate2.get_cuda_device_count() < 1:
                raise RuntimeError("Requested GPU unavailable")
        else:
            import torch

            if not torch.cuda.is_available():
                raise RuntimeError("Requested GPU unavailable")
            torch.cuda.reset_peak_memory_stats()

        def sample_memory():
            while not stop.is_set():
                try:
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                        capture_output=True,
                        text=True,
                        timeout=3,
                    )
                    if result.returncode == 0:
                        memory.extend(int(value.strip()) for value in result.stdout.splitlines())
                except (OSError, ValueError, subprocess.TimeoutExpired):
                    pass
                stop.wait(0.2)

        threading.Thread(target=sample_memory, daemon=True).start()
    load_start = time.perf_counter()
    decode_language = "ar" if samples[0][3] == "ary" else samples[0][3]
    parameter_dtypes = {}
    if args.backend == "whisper":
        from faster_whisper import WhisperModel

        precision = "int8" if args.device == "cpu" else "float16"
        model = WhisperModel(args.model, device=args.device, compute_type=precision, cpu_threads=4)
        decode_options = {"temperature": 0.0} if args.whisper_greedy else {}

        def infer(audio):
            segments, _ = model.transcribe(
                audio,
                beam_size=1,
                language=decode_language,
                vad_filter=False,
                condition_on_previous_text=False,
                **decode_options,
            )
            return " ".join(segment.text.strip() for segment in segments)

    elif args.backend == "qwen":
        from qwen_asr import Qwen3ASRModel

        precision = args.qwen_dtype
        model = Qwen3ASRModel.from_pretrained(
            args.model,
            dtype=getattr(torch, args.qwen_dtype),
            device_map="cuda:0",
            max_new_tokens=256,
        )
        core = getattr(model, "model", None)
        if core is not None and hasattr(core, "parameters"):
            for parameter in core.parameters():
                key = str(parameter.dtype)
                parameter_dtypes[key] = parameter_dtypes.get(key, 0) + parameter.numel()

        def infer(audio):
            name = {"en": "English", "fr": "French", "ar": "Arabic", "ary": "Arabic"}[
                decode_language
            ]
            return model.transcribe(audio=(audio, 16000), language=name)[0].text

    else:
        from transformers import AutoModelForTDT, AutoProcessor

        precision = "float16"
        processor = AutoProcessor.from_pretrained(
            args.model, local_files_only=True, trust_remote_code=False
        )
        model = (
            AutoModelForTDT.from_pretrained(
                args.model,
                local_files_only=True,
                trust_remote_code=False,
                torch_dtype=torch.float16,
            )
            .to(args.device)
            .eval()
        )

        def infer(audio):
            inputs = processor(audio, sampling_rate=16000, return_tensors="pt").to(
                args.device, dtype=torch.float16
            )
            with torch.inference_mode():
                outputs = model.generate(**inputs)
            sequences = outputs.sequences if hasattr(outputs, "sequences") else outputs
            return processor.batch_decode(sequences, skip_special_tokens=True)[0]

    load_seconds = time.perf_counter() - load_start
    # A separate silence sample warms kernels without consuming benchmark labels.
    silence_text = infer(np.zeros(16000, dtype=np.float32))
    if torch:
        torch.cuda.synchronize()
    report = {
        "backend": args.backend,
        "runner_source_sha256": runner_source_sha256,
        "model_directory": Path(args.model).name,
        "device": args.device,
        "precision": precision,
        "qwen_parameter_dtype_counts": parameter_dtypes,
        "whisper_temperature_policy": "fixed0"
        if args.whisper_greedy
        else "library-default-fallback",
        "silence_control": {
            "audio_seconds": 1,
            "language_hint": decode_language,
            "nonempty": bool(silence_text.strip()),
            "output_characters": len(silence_text.strip()),
            "output_sha256": hashlib.sha256(silence_text.encode()).hexdigest(),
            "scope": "single synthetic silence warmup; not a full no-speech validation",
        },
        "dataset": manifest["repo"],
        "dataset_revision": manifest["revision"],
        "license": manifest["license"],
        "roleplay": not bool(args.manifest),
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "normalization": "NFC/casefold/whitespace; punctuation retained",
        "protocol": "mono16kHz; fixed30s; English hint where supported; greedy/beam1; "
        "no VAD; warmup1s silence; load/warmup excluded",
        "load_seconds": load_seconds,
        "backend_version": importlib.metadata.version(
            {"whisper": "faster-whisper", "qwen": "qwen-asr", "parakeet": "transformers"}[
                args.backend
            ]
        ),
        "repetitions": args.repetitions,
        "expected_observations": len(samples) * args.repetitions,
        "observations": [],
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["numpy", "soundfile", "scipy", "rapidfuzz"]
        },
    }
    if args.manifest:
        report["sources"] = manifest["sources"]
        report["comparison_normalization"] = (
            "NFKC/casefold; punctuation/symbols to spaces; "
            "Arabic diacritics/tatweel removed; accents and letters retained"
        )
        report["protocol"] = report["protocol"].replace(
            "English hint", "French/Arabic hint (Darija uses Arabic mode)"
        )
    receipt = Path(args.model) / "download-receipt.json"
    if receipt.exists():
        report["model_receipt"] = json.loads(receipt.read_text(encoding="utf-8"))
    else:
        weights = []
        for path in sorted(Path(args.model).iterdir()):
            if path.suffix in (".bin", ".safetensors"):
                digest = hashlib.sha256()
                with path.open("rb") as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(block)
                weights.append({"file": path.name, "sha256": digest.hexdigest()})
        report["cached_weight_sha256"] = weights
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.private_predictions:
        args.private_predictions.parent.mkdir(parents=True, exist_ok=True)
        args.private_predictions.open("x", encoding="utf-8").close()
    for repeat in range(args.repetitions):
        for accent, audio, reference, language in samples:
            decode_language = "ar" if language == "ary" else language
            start = time.perf_counter()
            texts = [
                infer(audio[offset : offset + 480000]) for offset in range(0, len(audio), 480000)
            ]
            if torch:
                torch.cuda.synchronize()
            elapsed = time.perf_counter() - start
            hypothesis = normalize(" ".join(texts))
            comparison_reference = normalize_comparison(reference)
            comparison_hypothesis = normalize_comparison(hypothesis)
            row = {
                "sample": accent,
                "language": language,
                "repeat": repeat,
                "seconds": elapsed,
                "audio_seconds": len(audio) / 16000,
                "word_errors": distance(reference.split(), hypothesis.split()),
                "reference_words": len(reference.split()),
                "char_errors": distance(reference, hypothesis),
                "reference_chars": len(reference),
                "normalized_word_errors": distance(
                    comparison_reference.split(), comparison_hypothesis.split()
                ),
                "normalized_reference_words": len(comparison_reference.split()),
                "normalized_char_errors": distance(comparison_reference, comparison_hypothesis),
                "normalized_reference_chars": len(comparison_reference),
                "hypothesis_sha256": hashlib.sha256(hypothesis.encode()).hexdigest(),
            }
            report["observations"].append(row)
            report["peak_torch_allocated_bytes"] = (
                torch.cuda.max_memory_allocated() if torch else None
            )
            report["sampled_whole_gpu_peak_mib"] = max(memory) if memory else None
            args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
            if args.private_predictions:
                with args.private_predictions.open("a", encoding="utf-8") as private:
                    private.write(
                        json.dumps(
                            {
                                "sample_id": accent,
                                "language": language,
                                "repeat": repeat,
                                "scoring_reference": reference,
                                "prediction": " ".join(texts),
                                "scoring_prediction_sha256": row["hypothesis_sha256"],
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            print(
                args.backend,
                accent,
                repeat,
                round(elapsed, 2),
                round(row["word_errors"] / row["reference_words"], 4),
                flush=True,
            )
    stop.set()


if __name__ == "__main__":
    main()
