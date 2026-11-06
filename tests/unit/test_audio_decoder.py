"""Exercise the real faster-whisper/PyAV boundary without loading model weights."""

import io

from faster_whisper.audio import decode_audio

from tests.conftest import make_wav_bytes


def test_faster_whisper_decodes_synthetic_wav() -> None:
    samples = decode_audio(io.BytesIO(make_wav_bytes(duration_seconds=1.0)))
    assert samples.shape == (16000,)
    assert str(samples.dtype) == "float32"
    assert not samples.any()
