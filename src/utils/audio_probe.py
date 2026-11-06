"""Decode untrusted media in a short-lived process before accepting intake."""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

from src.utils.audio import (
    MAX_FILE_SIZE_BYTES,
    AudioValidationError,
    detect_audio_format,
    extract_audio_properties,
)


def container_probe_command(image: str, data: bytes) -> list[str]:
    """Use an immutable preinstalled image; never pull or mount host folders."""
    if re.fullmatch(r"sha256:[0-9a-f]{64}", image) is None:
        raise AudioValidationError("Container decoder requires an immutable local image ID")
    fmt = detect_audio_format(data)
    demuxer = {"wav": "wav", "mp3": "mp3", "flac": "flac", "m4a": "mov"}.get(fmt or "")
    if demuxer is None:
        raise AudioValidationError("Unsupported audio")
    expected = extract_audio_properties(data, fmt or "").duration_seconds
    worker = Path(__file__).with_name("container_audio_probe.py").read_text(encoding="utf-8")
    return [
        "docker",
        "run",
        "--rm",
        "--name",
        "project28-probe-" + uuid.uuid4().hex,
        "--pull=never",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--pids-limit=32",
        "--memory=1g",
        "--memory-swap=1g",
        "--cpus=1",
        "--user=65534:65534",
        "-i",
        "--entrypoint=python",
        image,
        "-c",
        worker,
        demuxer,
        str(expected),
    ]


def verify_decode(data: bytes, *, timeout_seconds: float = 30) -> None:
    """Contain decoder crashes and hangs; this is not an OS security sandbox."""
    if not 0 < len(data) <= MAX_FILE_SIZE_BYTES:
        raise AudioValidationError("Audio input exceeds decoder bounds")
    if not 0 < timeout_seconds <= 120:
        raise ValueError("Invalid decoder timeout")
    root = Path(__file__).resolve().parents[2]
    environment = {
        key: os.environ[key] for key in ("SYSTEMROOT", "PATH", "TEMP", "TMP") if key in os.environ
    }
    try:
        image = os.getenv("AUDIO_PROBE_CONTAINER_IMAGE")
        command = (
            container_probe_command(image, data)
            if image
            else [sys.executable, "-m", "src.utils.audio_probe"]
        )
        result = subprocess.run(
            command,
            input=data,
            capture_output=True,
            timeout=timeout_seconds,
            cwd=root,
            env=environment,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        if image and "--name" in command:
            name = command[command.index("--name") + 1]
            try:
                subprocess.run(
                    ["docker", "rm", "-f", name], capture_output=True, timeout=10, check=False
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
        raise AudioValidationError("Audio decoder failed or timed out") from exc
    if result.returncode != 0 or result.stdout.strip() != b"ok":
        raise AudioValidationError("Audio decoder rejected the recording")


def main() -> None:
    from src.utils.audio import MAX_DURATION_SECONDS, detect_audio_format, extract_audio_properties
    from src.utils.decoder_limits import apply_decoder_limits

    try:
        apply_decoder_limits()
        import av

        data = sys.stdin.buffer.read(MAX_FILE_SIZE_BYTES + 1)
        if not data or len(data) > MAX_FILE_SIZE_BYTES:
            raise ValueError("Input size")
        fmt = detect_audio_format(data)
        demuxer = {"wav": "wav", "mp3": "mp3", "flac": "flac", "m4a": "mov"}.get(fmt or "")
        if demuxer is None:
            raise ValueError("Format")
        seconds = 0.0
        with av.open(
            io.BytesIO(data), mode="r", format=demuxer, options={"protocol_whitelist": "file,pipe"}
        ) as container:
            if len(container.streams.audio) != 1:
                raise ValueError("Streams")
            for frame in container.decode(container.streams.audio[0]):
                if frame.sample_rate <= 0:
                    raise ValueError("Rate")
                seconds += frame.samples / frame.sample_rate
                if seconds > MAX_DURATION_SECONDS + 0.2:
                    raise ValueError("Duration")
        advertised = extract_audio_properties(data, fmt or "").duration_seconds
        if seconds <= 0 or seconds < advertised - max(0.2, advertised * 0.02):
            raise ValueError("Incomplete decode")
        sys.stdout.write("ok")
    except Exception:
        # Decoder/library diagnostics and input metadata must not escape to logs.
        sys.exit(1)


if __name__ == "__main__":
    main()
