"""Speaker alignment and opt-in pipeline boundaries using synthetic turns."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.agents import transcription
from src.agents.diarization import CommunityDiarizer, SpeakerTurn, align_turn, load_community
from tests.conftest import make_intake_result


def test_neural_roles_are_unknown_without_grounded_channels() -> None:
    turns = [SpeakerTurn(0, 1.5, "speaker-1"), SpeakerTurn(1.5, 3, "speaker-2")]
    assert align_turn(0, 1, turns).speaker_id == "speaker-1"
    assert align_turn(0, 1, turns).role == "Unknown"
    assert align_turn(4, 5, turns).speaker_id is None
    assert not align_turn(0, 3, turns).overlap  # sequential turns do not overlap
    assert align_turn(0, 3, turns).speaker_id is None  # equal-duration tie


def test_overlap_and_explicit_channel_roles() -> None:
    turns = [SpeakerTurn(0, 2, "a", 0), SpeakerTurn(1, 3, "b", 1)]
    answer = align_turn(0, 1.5, turns, {0: "Agent", 1: "Customer"})
    assert (answer.speaker_id, answer.role, answer.overlap) == ("a", "Agent", True)
    ambiguous = turns + [SpeakerTurn(0, 1, "a", None)]
    assert align_turn(0, 1, ambiguous, {0: "Agent"}).role == "Unknown"


def test_duplicate_intervals_do_not_inflate_speaker_duration() -> None:
    turns = [SpeakerTurn(0, 1, "a"), SpeakerTurn(0, 1, "a"), SpeakerTurn(0.2, 1.4, "b")]
    assert align_turn(0, 2, turns).speaker_id == "b"


def test_invalid_turn_and_remote_model_fail_closed() -> None:
    with pytest.raises(ValueError):
        SpeakerTurn(2, 1, "a")
    with pytest.raises(ValueError):
        load_community("pyannote/speaker-diarization-community-1")
    assert align_turn(float("nan"), 2, []).role == "Unknown"


def test_pipeline_adapter_extracts_neural_turns() -> None:
    annotation = MagicMock()
    annotation.itertracks.return_value = [(SimpleNamespace(start=0.0, end=1.0), "t", "SPEAKER_00")]
    adapter = CommunityDiarizer(lambda _: SimpleNamespace(speaker_diarization=annotation))
    assert adapter.turns("recording.wav") == [SpeakerTurn(0, 1, "SPEAKER_00")]


def test_loader_uses_local_directory_and_optional_runtime(tmp_path, monkeypatch) -> None:
    import src.agents.diarization as diarization

    load_community.cache_clear()
    pipeline = MagicMock()
    module = SimpleNamespace(Pipeline=SimpleNamespace(from_pretrained=lambda path: pipeline))
    monkeypatch.setattr(diarization.importlib, "import_module", lambda name: module)
    assert load_community(str(tmp_path)).pipeline is pipeline
    load_community.cache_clear()


def test_neural_mode_bypasses_heuristic_cache_and_preserves_unknown_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DIARIZATION_BACKEND", "pyannote")
    monkeypatch.setenv("DIARIZATION_MODEL_PATH", "unused-by-mock")
    model = MagicMock()
    model.transcribe.return_value = (
        iter(
            [
                SimpleNamespace(
                    text="hello", start=0.0, end=1.0, avg_logprob=-0.1, no_speech_prob=0.1
                )
            ]
        ),
        MagicMock(),
    )
    monkeypatch.setattr(transcription, "_get_whisper_model", lambda _: model)
    monkeypatch.setattr(transcription, "_compute_audio_hash", lambda _: "hash")
    check = MagicMock()
    save = MagicMock()
    monkeypatch.setattr(transcription, "_check_cache", check)
    monkeypatch.setattr(transcription, "_save_cache", save)
    monkeypatch.setattr(
        transcription,
        "load_community",
        lambda _: SimpleNamespace(turns=lambda _path: [SpeakerTurn(0, 1, "SPEAKER_00")]),
    )
    result = transcription.run_transcription(make_intake_result(), db_engine=MagicMock())
    assert result.segments[0].speaker == "Unknown"
    assert result.segments[0].speaker_id == "SPEAKER_00"
    assert result.segments[0].speaker_role == "Unknown"
    check.assert_not_called()
    save.assert_not_called()


def test_invalid_backend_is_not_silently_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIARIZATION_BACKEND", "invalid")
    with pytest.raises(ValueError, match="Unsupported"):
        transcription.run_transcription(make_intake_result())


def test_explicit_channel_roles_are_passed_to_neural_alignment(monkeypatch) -> None:
    monkeypatch.setenv("DIARIZATION_BACKEND", "pyannote")
    monkeypatch.setenv("DIARIZATION_MODEL_PATH", "local-model")
    model = MagicMock()
    model.transcribe.return_value = (
        iter(
            [
                SimpleNamespace(
                    text="hello", start=0.0, end=1.0, avg_logprob=-0.1, no_speech_prob=0.1
                )
            ]
        ),
        MagicMock(),
    )
    monkeypatch.setattr(transcription, "_get_whisper_model", lambda _: model)
    diarizer = MagicMock()
    diarizer.channel_turns.return_value = [SpeakerTurn(0, 1, "ch0:speaker", 0)]
    monkeypatch.setattr(transcription, "load_community", lambda _: diarizer)
    result = transcription.run_transcription(
        make_intake_result(), channel_roles={0: "Agent", 1: "Customer"}
    )
    assert result.segments[0].speaker_role == "Agent"
    diarizer.turns.assert_not_called()


def test_channel_role_map_must_be_explicit_and_complete(monkeypatch) -> None:
    monkeypatch.setenv("DIARIZATION_BACKEND", "pyannote")
    with pytest.raises(ValueError, match="Trusted channel roles"):
        transcription.run_transcription(make_intake_result(), channel_roles={0: "Agent"})


def test_workflow_passes_explicit_channel_roles_to_transcription(monkeypatch) -> None:
    from src.graph import workflow

    run = MagicMock(return_value=MagicMock())
    monkeypatch.setattr(workflow, "run_transcription", run)
    config = SimpleNamespace(
        confidence_threshold=0.3, low_confidence_halt_ratio=0.8, whisper_model_size="base"
    )
    roles = {0: "Agent", 1: "Customer"}
    workflow.transcription_node({"intake": make_intake_result(), "channel_roles": roles}, config)
    assert run.call_args.kwargs["channel_roles"] == roles


def test_service_forwards_explicit_channel_roles(tmp_path) -> None:
    from src.services.pipeline import process_call

    audio = tmp_path / "input.wav"
    audio.write_bytes(b"test fixture")
    graph = MagicMock()
    graph.invoke.return_value = {"status": "failed", "error": "test"}
    roles = {0: "Agent", 1: "Customer"}
    process_call(audio, None, None, graph, MagicMock(), MagicMock(), channel_roles=roles)
    assert graph.invoke.call_args.args[0]["channel_roles"] == roles
