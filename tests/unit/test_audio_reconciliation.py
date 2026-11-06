from types import SimpleNamespace

import numpy as np

from src.utils.audio_preprocessing import AudioChunk, PreparedAudio, contextual_windows
from src.utils.audio_reconciliation import owned_segment


def test_context_windows_retain_disjoint_original_ownership():
    windows = iter(
        [
            (0, PreparedAudio(np.ones((1, 8), dtype=np.float32), 4, 1, "wav")),
            (8, PreparedAudio(np.ones((1, 8), dtype=np.float32) * 2, 4, 1, "wav")),
        ]
    )
    output = list(contextual_windows(windows, context_samples=2))
    assert [(offset, a.core_start, a.core_end) for offset, a in output] == [(0, 0, 8), (6, 2, 10)]
    assert [a.samples.shape[1] for _, a in output] == [10, 10]


def test_context_words_are_emitted_once_and_preserve_text():
    words = [
        SimpleNamespace(word=" hello", start=0.5, end=1.5),
        SimpleNamespace(word=" world", start=1.5, end=2.5),
    ]
    segment = SimpleNamespace(words=words, avg_logprob=-0.1, no_speech_prob=0.1)
    first = owned_segment(segment, AudioChunk(0, 48000, core_start=0, core_end=24000))
    second = owned_segment(segment, AudioChunk(0, 48000, core_start=24000, core_end=48000))
    assert first.text == " hello"
    assert second.text == " world"
