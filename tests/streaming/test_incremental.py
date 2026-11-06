"""Deterministic ownership/revision/VAD gates; fake decoder results are not quality metrics."""

from dataclasses import replace

import pytest

from ml.asr.incremental import Reconciler, SpeechWindows, Window, Word, normalize_token

VOICE = b"\xb8\x0b" * 16000
SILENCE = b"\0" * 32000


def window(
    *,
    final=False,
    start=0,
    end=2,
    own_start=None,
    own_end=None,
    identifier="00000000-0000-4000-8000-000000000001",
):
    return Window(
        identifier,
        int(start * 16000),
        int(end * 16000),
        int((start if own_start is None else own_start) * 16000),
        int((end if own_end is None else own_end) * 16000),
        SILENCE * int(end - start),
        final,
        "silence" if final else "partial",
    )


def test_silence_never_schedules_recognition_and_preroll_is_bounded():
    track = SpeechWindows()
    for i in range(20):
        assert track.push(SILENCE, i * 16000) == []
        assert len(track.buffer) <= 6400
    assert track.flush() is None


def test_two_second_partials_and_vad_endpoint_preserve_original_sample_clock():
    track = SpeechWindows()
    assert track.push(VOICE, 0) == []
    interim = track.push(VOICE, 16000)
    assert len(interim) == 1 and not interim[0].final
    assert interim[0].start_sample == 0 and interim[0].end_sample == 32000
    final = track.push(SILENCE, 32000)
    assert len(final) == 1 and final[0].final and final[0].reason == "silence"
    assert final[0].end_sample == 41600
    assert final[0].utterance_id == interim[0].utterance_id


def test_long_speech_windows_overlap_but_final_ownership_does_not():
    track = SpeechWindows()
    results = []
    for i in range(17):
        results.extend(track.push(VOICE, i * 16000))
        assert len(track.buffer) <= 256000
    results.append(track.flush())
    finals = [w for w in results if w.final]
    assert len(finals) == 3
    assert [(w.owned_start / 16000, w.owned_end / 16000) for w in finals] == [
        (0, 7),
        (7, 13),
        (13, 17),
    ]
    assert finals[1].start_sample < finals[0].end_sample
    assert len({w.utterance_id for w in finals}) == 3
    assert all(len(w.pcm) <= 256000 for w in results)


def test_manual_flush_closes_only_current_turn_and_cannot_duplicate_it():
    track = SpeechWindows()
    track.push(VOICE, 0)
    result = track.flush()
    assert result.final and result.reason == "manual" and result.end_sample == 16000
    assert track.flush() is None
    track.push(VOICE, 16000)
    assert track.flush().utterance_id != result.utterance_id


@pytest.mark.parametrize("pcm,offset", [(b"\0" * 2, 0), (VOICE, 16000)], ids=["bad-length", "gap"])
def test_bad_pcm_or_gap_rejected(pcm, offset):
    with pytest.raises(ValueError):
        SpeechWindows().push(pcm, offset)


def test_midword_and_punctuation_are_revisions_not_appended_text():
    engine = Reconciler()
    current = window()
    a = engine.apply(current, [Word(0, 1, " Transcrip-")])
    b = engine.apply(
        replace(current, end_sample=48000, pcm=SILENCE * 3),
        [Word(0, 1, " Transcription"), Word(1, 2, " works.")],
    )
    assert (a.revision, b.revision) == (1, 2)
    assert b.text == "Transcription works."
    final = engine.apply(
        replace(current, final=True, reason="silence"),
        [Word(0, 1, " Transcription"), Word(1, 2, " works!")],
    )
    assert final.state == "final" and final.agreed_prefix_words == 2
    assert engine.apply(current, [Word(0, 1, " altered")]) is None


def test_duplicate_partial_text_suppressed_but_final_transition_emitted():
    engine = Reconciler()
    current = window()
    words = [Word(0, 1, " Hello.")]
    assert engine.apply(current, words).revision == 1
    assert engine.apply(current, words) is None
    assert engine.apply(replace(current, final=True), words).revision == 2


def test_overlap_ownership_and_timed_suffix_reconciliation():
    engine = Reconciler()
    first = window(final=True, start=0, end=8, own_end=7)
    result = engine.apply(
        first, [Word(5.8, 6.2, " Please"), Word(6.5, 7.1, " verify."), Word(7.2, 7.8, " the")]
    )
    assert result.text == "Please verify."
    second = window(
        final=True, start=6, end=10, own_start=7, identifier="00000000-0000-4000-8000-000000000002"
    )
    result = engine.apply(
        second, [Word(0.9, 1.2, " verify!"), Word(1.3, 2, " the"), Word(2, 3, " connection.")]
    )
    assert result.text == "the connection."
    assert result.start == 7 and result.end == 10


def test_legitimate_repeated_word_after_timed_gap_is_preserved():
    engine = Reconciler()
    engine.apply(window(final=True), [Word(0, 0.4, " No.")])
    second = window(final=True, start=2, end=4, identifier="00000000-0000-4000-8000-000000000002")
    assert engine.apply(second, [Word(0, 0.4, " No."), Word(0.5, 1, " no!")]).text == "No. no!"


def test_failure_recovers_with_a_new_revision():
    engine = Reconciler()
    current = window()
    first = engine.apply(current, [Word(0, 1, " hello")])
    failed = engine.apply(current, [], failed=True)
    recovered = engine.apply(replace(current, final=True), [Word(0, 1, " hello")])
    assert [first.state, failed.state, recovered.state] == ["provisional", "failed", "final"]
    assert [first.revision, failed.revision, recovered.revision] == [1, 2, 3]


def test_invalid_word_timestamps_are_never_exposed():
    result = Reconciler().apply(
        window(final=True),
        [Word(float("nan"), 1, "bad"), Word(0, 9, "outside"), Word(0, 1, " good")],
    )
    assert result.text == "good"


def test_unicode_boundary_matching_is_not_limited_to_english():
    assert normalize_token("Bonjour!") == normalize_token("BONJOUR.")
    assert normalize_token("مرحبا،") == normalize_token("مرحبا")


def test_benchmark_percentiles_handle_small_and_empty_samples():
    from scripts.benchmark_incremental_asr import percentiles

    assert percentiles([1.0, 3.0]) == {"n": 2, "p50": 2.0, "p95": 3.0}
    assert percentiles([]) == {"n": 0, "p50": None, "p95": None}
