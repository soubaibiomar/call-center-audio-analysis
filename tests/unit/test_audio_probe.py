"""Real subprocess validation and timeout handling for untrusted audio."""

import subprocess

import pytest

from src.utils.audio import AudioValidationError
from src.utils.audio_probe import container_probe_command, verify_decode
from tests.unit.test_audio_preprocessing import make_encoded


def test_probe_accepts_real_audio_and_rejects_truncated_mp3():
    verify_decode(make_encoded("wav", "pcm_s16le"))
    data = make_encoded("mp3", "libmp3lame", silent=False)
    with pytest.raises(AudioValidationError):
        verify_decode(data[: int(len(data) * 0.7)])


def test_probe_timeout_fails_closed(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("decoder", 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(AudioValidationError, match="timed out"):
        verify_decode(b"test")


def test_intake_rejects_truncated_mp3_before_persisting_audio():
    from src.agents.intake import run_intake
    from src.graph.state import AudioInput

    data = make_encoded("mp3", "libmp3lame", silent=False)
    result = run_intake(AudioInput(audio_data=data[: int(len(data) * 0.7)], filename="damaged.mp3"))
    assert not result.validation_passed
    assert result.audio_path == ""


def test_operating_system_rejects_over_limit_allocation():
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from src.utils.decoder_limits import apply_decoder_limits; "
            "apply_decoder_limits(64*1024*1024); block=bytearray(256*1024*1024)",
        ],
        capture_output=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert b"MemoryError" in result.stderr


def test_intake_checks_expected_source_digest_before_decoding():
    import hashlib

    from src.agents.intake import run_intake
    from src.graph.state import AudioInput

    data = make_encoded("wav", "pcm_s16le")
    expected = hashlib.sha256(data).hexdigest()
    damaged = data[:-2]
    result = run_intake(AudioInput(audio_data=damaged, filename="x.wav", expected_sha256=expected))
    assert not result.validation_passed
    assert "checksum" in result.validation_error


def test_container_probe_requires_pinned_image_and_permission_restrictions():
    data = make_encoded("wav", "pcm_s16le")
    with pytest.raises(AudioValidationError, match="immutable"):
        container_probe_command("latest", data)
    command = container_probe_command("sha256:" + "a" * 64, data)
    for option in (
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--user=65534:65534",
        "--memory=1g",
        "--memory-swap=1g",
        "--pull=never",
    ):
        assert option in command
    assert "--mount" not in command and "--volume" not in command


def test_container_timeout_removes_only_its_own_named_container(monkeypatch):
    monkeypatch.setenv("AUDIO_PROBE_CONTAINER_IMAGE", "sha256:" + "a" * 64)
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if len(calls) == 1:
            raise subprocess.TimeoutExpired(command, 1)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(AudioValidationError, match="timed out"):
        verify_decode(make_encoded("wav", "pcm_s16le"))
    generated_name = calls[0][calls[0].index("--name") + 1]
    assert calls[1] == ["docker", "rm", "-f", generated_name]
    assert generated_name.startswith("project28-probe-")
