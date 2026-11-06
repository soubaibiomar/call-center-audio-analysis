"""Exercise actual FFmpeg codecs and the bundled Silero model with synthetic data."""

import io

import av
import numpy as np
import pytest

from src.utils.audio import AudioValidationError, validate_audio_file
from src.utils.audio_preprocessing import (
    AudioChunk,
    PreparedAudio,
    decode_resample,
    has_severe_phase_cancellation,
    iter_resampled_windows,
    speech_chunks,
)


def make_encoded(container: str, codec: str, *, silent: bool = True, rate: int = 16000) -> bytes:
    output = io.BytesIO()
    with av.open(output, mode="w", format=container) as destination:
        stream = destination.add_stream(codec, rate=rate)
        stream.layout = "stereo"
        for block in range(rate // 1000):
            samples = np.zeros((2, 1000), dtype=np.float32)
            if not silent:
                t = (np.arange(1000) + block * 1000) / rate
                samples[0] = 0.3 * np.sin(2 * np.pi * 440 * t)
                samples[1] = 0.3 * np.sin(2 * np.pi * 880 * t)
            frame = av.AudioFrame.from_ndarray(samples, format="fltp", layout="stereo")
            frame.sample_rate = rate
            for packet in stream.encode(frame):
                destination.mux(packet)
        for packet in stream.encode(None):
            destination.mux(packet)
    return output.getvalue()


@pytest.mark.parametrize(
    ("container", "codec", "extension"),
    [
        ("wav", "pcm_s16le", "wav"),
        ("mp3", "libmp3lame", "mp3"),
        ("flac", "flac", "flac"),
        ("mp4", "aac", "m4a"),
    ],
)
def test_real_codec_decoding_preserves_stereo(container, codec, extension) -> None:
    audio = decode_resample(make_encoded(container, codec, silent=False), "fixture." + extension)
    assert audio.sample_rate == 16000
    assert audio.original_channels == 2
    assert audio.samples.shape[0] == 2
    assert 0.9 <= audio.samples.shape[1] / audio.sample_rate <= 1.2
    frequencies = np.fft.rfftfreq(audio.samples.shape[1], 1 / audio.sample_rate)
    peaks = frequencies[np.argmax(np.abs(np.fft.rfft(audio.samples, axis=1)), axis=1)]
    assert abs(peaks[0] - 440) < 4 and abs(peaks[1] - 880) < 4


def test_malformed_header_fails_validation_and_decoding() -> None:
    payload = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"not an audio stream"
    assert not validate_audio_file(payload, "bad.wav").is_valid
    with pytest.raises(AudioValidationError):
        decode_resample(payload, "bad.wav")


def test_truncated_wav_with_valid_header_is_rejected() -> None:
    payload = make_encoded("wav", "pcm_s16le")[:60]
    assert not validate_audio_file(payload, "truncated.wav").is_valid
    with pytest.raises(AudioValidationError):
        decode_resample(payload, "truncated.wav")


def test_float_wav_is_supported_and_truncation_rejected() -> None:
    import soundfile as sf

    output = io.BytesIO()
    sf.write(output, np.zeros(16000, dtype=np.float32), 16000, format="WAV", subtype="FLOAT")
    data = output.getvalue()
    assert validate_audio_file(data, "float.wav").is_valid
    assert decode_resample(data, "float.wav").samples.shape == (1, 16000)
    assert not validate_audio_file(data[:-500], "truncated-float.wav").is_valid


def test_truncated_mp3_with_duration_header_is_rejected() -> None:
    data = make_encoded("mp3", "libmp3lame", silent=False)
    with pytest.raises(AudioValidationError):
        decode_resample(data[: int(len(data) * 0.7)], "truncated.mp3")


def test_distinct_stereo_is_not_mistaken_for_phase_cancellation() -> None:
    data = make_encoded("wav", "pcm_s16le", silent=False)
    assert not has_severe_phase_cancellation(data, "stereo.wav")


def test_short_cancelled_section_is_not_hidden_by_other_stereo_audio() -> None:
    import wave

    t = np.arange(16000) / 16000
    left = (np.sin(2 * np.pi * 440 * t) * 12000).astype("<i2")
    right = (np.sin(2 * np.pi * 880 * t) * 12000).astype("<i2")
    stereo = np.concatenate((np.column_stack((left, -left)), np.column_stack((left, right))))
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(stereo.astype("<i2").tobytes())
    assert has_severe_phase_cancellation(output.getvalue(), "partial.wav")


def test_vad_preserves_opposite_phase_and_independent_stereo(monkeypatch) -> None:
    import faster_whisper.vad as vad

    seen = []

    def detect(samples, *args, **kwargs):
        seen.append(samples.copy())
        return [{"start": 0, "end": len(samples)}] if np.any(samples) else []

    monkeypatch.setattr(vad, "get_speech_timestamps", detect)
    signal = np.linspace(-0.5, 0.5, 16000, dtype=np.float32)
    opposite = PreparedAudio(np.stack((signal, -signal)), 16000, 2, "wav")
    chunks = speech_chunks(opposite)
    assert len(chunks) == 1 and chunks[0].channel == 0
    np.testing.assert_array_equal(seen[0], signal)
    seen.clear()
    distinct = PreparedAudio(np.stack((signal, signal * 0.1)), 16000, 2, "wav")
    assert {chunk.channel for chunk in speech_chunks(distinct)} == {0, 1}
    assert len(seen) == 2


def test_ffmpeg_resamples_48khz_stereo_without_duration_drift() -> None:
    audio = decode_resample(make_encoded("wav", "pcm_s16le", silent=False, rate=48000), "x.wav")
    assert audio.samples.shape == (2, 16000)


def test_windowed_resampling_preserves_every_sample_and_offset() -> None:
    import wave

    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        wav.writeframes(bytes(48000 * 2 * 2 + 48000))
    data = output.getvalue()
    windows = list(iter_resampled_windows(data, "x.wav", window_seconds=1))
    assert [start for start, _ in windows] == [0, 16000, 32000]
    assert [audio.samples.shape[1] for _, audio in windows] == [16000, 16000, 8000]
    np.testing.assert_array_equal(
        np.concatenate([audio.samples for _, audio in windows], axis=1),
        decode_resample(data, "x.wav").samples,
    )


def test_silero_silence_and_sample_coordinate_roundtrip() -> None:
    audio = decode_resample(make_encoded("wav", "pcm_s16le"), "silent.wav")
    assert speech_chunks(audio) == []
    chunk = AudioChunk(160000, 240000)
    assert chunk.absolute_seconds(1.25) == 11.25
    with pytest.raises(ValueError):
        chunk.absolute_seconds(5.001)


def test_chunk_splitting_retains_exact_original_sample_offsets(monkeypatch) -> None:
    import faster_whisper.vad as vad

    audio = decode_resample(make_encoded("wav", "pcm_s16le"), "fixture.wav")
    monkeypatch.setattr(
        vad, "get_speech_timestamps", lambda *args, **kwargs: [{"start": 1, "end": 15999}]
    )
    chunks = speech_chunks(audio, max_chunk_seconds=0.25)
    assert [(c.core_start, c.core_end) for c in chunks] == [
        (1, 4001),
        (4001, 8001),
        (8001, 12001),
        (12001, 15999),
    ]
    assert chunks[-1].absolute_seconds((15999 - chunks[-1].start_sample) / 16000) == pytest.approx(
        15999 / 16000
    )


def test_opt_in_transcription_reconciles_chunk_times(monkeypatch, tmp_path) -> None:
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from src.agents import transcription
    from tests.conftest import make_intake_result

    path = tmp_path / "fixture.wav"
    path.write_bytes(make_encoded("wav", "pcm_s16le"))
    intake = make_intake_result()
    intake.audio_path = str(path)
    monkeypatch.setenv("AUDIO_PREPROCESS_SEGMENTS", "true")
    monkeypatch.setenv("DIARIZATION_BACKEND", "heuristic")
    monkeypatch.setattr(transcription, "speech_chunks", lambda _: [AudioChunk(8000, 16000)])
    model = MagicMock()
    model.transcribe.return_value = (
        iter(
            [
                SimpleNamespace(
                    text="hello", start=0.1, end=0.3, avg_logprob=-0.1, no_speech_prob=0.1
                )
            ]
        ),
        None,
    )
    monkeypatch.setattr(transcription, "_get_whisper_model", lambda _: model)
    result = transcription.run_transcription(intake)
    assert result.segments[0].start_time == pytest.approx(0.6)
    assert result.segments[0].end_time == pytest.approx(0.8)
    assert model.transcribe.call_args.kwargs["vad_filter"] is False


def test_opt_in_transcription_rejects_out_of_chunk_timestamp(monkeypatch, tmp_path) -> None:
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from src.agents import transcription
    from tests.conftest import make_intake_result

    path = tmp_path / "fixture.wav"
    path.write_bytes(make_encoded("wav", "pcm_s16le"))
    intake = make_intake_result()
    intake.audio_path = str(path)
    monkeypatch.setenv("AUDIO_PREPROCESS_SEGMENTS", "true")
    monkeypatch.setattr(transcription, "speech_chunks", lambda _: [AudioChunk(8000, 16000)])
    model = MagicMock()
    model.transcribe.return_value = (
        iter([SimpleNamespace(text="hello", start=0.1, end=0.8)]),
        None,
    )
    monkeypatch.setattr(transcription, "_get_whisper_model", lambda _: model)
    with pytest.raises(ValueError, match="outside chunk"):
        transcription.run_transcription(intake)


def test_stereo_transcription_uses_individual_channels_in_time_order(monkeypatch, tmp_path) -> None:
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from src.agents import transcription
    from tests.conftest import make_intake_result

    path = tmp_path / "fixture.wav"
    path.write_bytes(make_encoded("wav", "pcm_s16le", silent=False))
    intake = make_intake_result()
    intake.audio_path = str(path)
    monkeypatch.setenv("AUDIO_PREPROCESS_SEGMENTS", "true")
    monkeypatch.setenv("DIARIZATION_BACKEND", "heuristic")
    monkeypatch.setattr(
        transcription,
        "speech_chunks",
        lambda _: [AudioChunk(0, 16000, channel=0), AudioChunk(0, 16000, channel=1)],
    )
    model = MagicMock()
    seen = []

    def transcribe(samples, **kwargs):
        seen.append(samples.copy())
        time, text = (0.6, "later") if len(seen) == 1 else (0.2, "earlier")
        return iter(
            [
                SimpleNamespace(
                    text=text, start=time, end=time + 0.1, avg_logprob=-0.1, no_speech_prob=0.1
                )
            ]
        ), None

    model.transcribe.side_effect = transcribe
    monkeypatch.setattr(transcription, "_get_whisper_model", lambda _: model)
    result = transcription.run_transcription(intake)
    assert len(seen) == 2 and not np.array_equal(seen[0], seen[1])
    assert [segment.text for segment in result.segments] == ["earlier", "later"]


def test_phase_cancellation_automatically_selects_segmented_transcription(
    monkeypatch, tmp_path
) -> None:
    import wave
    from unittest.mock import MagicMock

    from src.agents import transcription
    from tests.conftest import make_intake_result

    path = tmp_path / "stereo.wav"
    signal = (np.sin(np.arange(16000) * 0.1) * 16000).astype("<i2")
    samples = np.column_stack((signal, -signal)).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(samples.tobytes())
    assert has_severe_phase_cancellation(path.read_bytes(), str(path))
    intake = make_intake_result()
    intake.audio_path = str(path)
    intake.audio_properties.channels = 2
    monkeypatch.delenv("AUDIO_PREPROCESS_SEGMENTS", raising=False)
    monkeypatch.setenv("DIARIZATION_BACKEND", "heuristic")
    monkeypatch.setattr(transcription, "speech_chunks", lambda _: [])
    model = MagicMock()
    monkeypatch.setattr(transcription, "_get_whisper_model", lambda _: model)
    transcription.run_transcription(intake)
    model.transcribe.assert_not_called()  # empty VAD result proves chunk path was selected
