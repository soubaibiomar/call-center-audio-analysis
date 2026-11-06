"""Run cached Whisper on CUDA/float16; no CPU fallback or transcript publication."""

import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import ctranslate2
from faster_whisper import WhisperModel

from services.workers.runtime import verify_cuda_runtime


def main() -> None:
    verify_cuda_runtime()
    start = perf_counter()
    model = WhisperModel("tiny", device="cuda", compute_type="float16", local_files_only=True)
    load_seconds = perf_counter() - start
    with TemporaryDirectory(prefix="project28-gpu-probe-") as directory:
        clip = Path(directory) / "sample.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                "data/samples/sample_01.mp3",
                "-t",
                "10",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-y",
                str(clip),
            ],
            check=True,
            capture_output=True,
        )
        start = perf_counter()
        segments, info = model.transcribe(str(clip), beam_size=1)
        count = sum(1 for _ in segments)  # Consume lazy results to execute real GPU kernels.
        elapsed = perf_counter() - start
    if model.model.device != "cuda" or model.model.compute_type != "float16" or count < 1:
        raise RuntimeError("CUDA transcription did not meet the verification contract")
    print(
        json.dumps(
            {
                "success": True,
                "cuda_devices": ctranslate2.get_cuda_device_count(),
                "device": model.model.device,
                "compute_type": model.model.compute_type,
                "clip_seconds": 10,
                "load_seconds": load_seconds,
                "transcription_seconds": elapsed,
                "segments": count,
                "language": info.language,
            }
        )
    )


if __name__ == "__main__":
    main()
