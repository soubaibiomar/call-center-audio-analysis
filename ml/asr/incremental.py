"""Speech windows and revision reconciliation, independent of transport and inference."""

import math
import unicodedata
from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

import numpy as np

SAMPLE_RATE = 16000
FRAME_SAMPLES = 320
MAX_WINDOW_SAMPLES = 8 * SAMPLE_RATE
CONTEXT_SAMPLES = SAMPLE_RATE
PARTIAL_STRIDE = 2 * SAMPLE_RATE

Reason = Literal["silence", "window_limit", "manual", "partial"]


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Window:
    utterance_id: str
    start_sample: int
    end_sample: int
    owned_start: int
    owned_end: int
    pcm: bytes
    final: bool
    reason: Reason


class SpeechWindows:
    """20 ms RMS VAD, 60 ms onset, 600 ms hangover; bounded overlapping turns.

    This is an explicit energy heuristic, not a trained speech/noise classifier.
    Each forced final owns only the first seven seconds, retaining context/tail.
    """

    def __init__(self, threshold: float = 0.015) -> None:
        if not 0 < threshold < 1:
            raise ValueError("VAD threshold must be a normalized RMS energy")
        self.threshold = threshold
        self.position = 0
        self.buffer = bytearray()
        self.buffer_start = 0
        self.utterance_id: str | None = None
        self.owned_start = 0
        self.last_partial = 0
        self.voice_frames = 0
        self.quiet_frames = 0

    def _window(
        self, end: int, *, final: bool, reason: Reason, owned_end: int | None = None
    ) -> Window:
        if self.utterance_id is None:
            raise ValueError("No active utterance")
        return Window(
            self.utterance_id,
            self.buffer_start,
            end,
            self.owned_start,
            end if owned_end is None else owned_end,
            bytes(self.buffer[: (end - self.buffer_start) * 2]),
            final,
            reason,
        )

    def push(self, pcm: bytes, start_sample: int) -> list[Window]:
        if len(pcm) != SAMPLE_RATE * 2 or start_sample != self.position:
            raise ValueError("Expected one contiguous second of mono PCM16LE")
        windows: list[Window] = []
        samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        energies = np.sqrt(np.mean(samples.reshape(-1, FRAME_SAMPLES) ** 2, axis=1))
        for i, rms in enumerate(energies):
            frame = pcm[i * FRAME_SAMPLES * 2 : (i + 1) * FRAME_SAMPLES * 2]
            self.buffer.extend(frame)
            self.position += FRAME_SAMPLES
            voiced = float(rms) >= self.threshold
            self.voice_frames = self.voice_frames + 1 if voiced else 0
            if self.utterance_id is None:
                # Keep 200 ms of pre-roll, including the onset detection frames.
                if len(self.buffer) > 6400:
                    removed = len(self.buffer) - 6400
                    del self.buffer[:removed]
                    self.buffer_start += removed // 2
                if self.voice_frames >= 3:
                    self.utterance_id = str(uuid4())
                    self.owned_start = self.buffer_start
                    self.last_partial = self.owned_start
                    self.quiet_frames = 0
                continue
            self.quiet_frames = 0 if voiced else self.quiet_frames + 1
            if self.quiet_frames >= 30:
                windows.append(self._window(self.position, final=True, reason="silence"))
                self.buffer.clear()
                self.buffer_start = self.position
                self.utterance_id = None
                self.voice_frames = self.quiet_frames = 0
            elif self.position - self.buffer_start >= MAX_WINDOW_SAMPLES:
                cut = self.position - CONTEXT_SAMPLES
                windows.append(
                    self._window(self.position, final=True, reason="window_limit", owned_end=cut)
                )
                # Next turn sees one second of finalized context plus one unowned tail second.
                next_start = cut - CONTEXT_SAMPLES
                del self.buffer[: (next_start - self.buffer_start) * 2]
                self.buffer_start, self.owned_start = next_start, cut
                self.utterance_id = str(uuid4())
                self.last_partial = cut
            elif self.position - self.last_partial >= PARTIAL_STRIDE:
                windows.append(self._window(self.position, final=False, reason="partial"))
                self.last_partial = self.position
        return windows

    def flush(self) -> Window | None:
        window = (
            self._window(self.position, final=True, reason="manual") if self.utterance_id else None
        )
        self.buffer.clear()
        self.buffer_start = self.position
        self.utterance_id = None
        self.voice_frames = self.quiet_frames = 0
        return window


def normalize_token(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def render_words(words: list[Word]) -> str:
    # Whisper tokens include leading whitespace, including language-specific punctuation.
    return "".join(word.text for word in words).strip()


@dataclass
class HypothesisState:
    revision: int = 0
    words: list[Word] = field(default_factory=list)
    final: bool = False
    failed: bool = False


@dataclass(frozen=True)
class Revision:
    utterance_id: str
    revision: int
    state: Literal["provisional", "final", "failed"]
    start: float
    end: float
    text: str
    agreed_prefix_words: int
    reason: Reason


class Reconciler:
    """One replaceable hypothesis per utterance, monotonic revisions and immutable finals."""

    def __init__(self) -> None:
        self.states: dict[str, HypothesisState] = {}
        self.final_tail: list[Word] = []

    def apply(self, window: Window, words: list[Word], *, failed: bool = False) -> Revision | None:
        state = self.states.setdefault(window.utterance_id, HypothesisState())
        if state.final:
            return None
        start = window.owned_start / SAMPLE_RATE
        end = window.owned_end / SAMPLE_RATE
        shifted = []
        for word in words[:500]:
            if (
                not math.isfinite(word.start)
                or not math.isfinite(word.end)
                or not 0 <= word.start < word.end <= len(window.pcm) / 32000 + 0.01
            ):
                continue
            absolute = Word(
                word.start + window.start_sample / SAMPLE_RATE,
                word.end + window.start_sample / SAMPLE_RATE,
                word.text,
            )
            midpoint = (absolute.start + absolute.end) / 2
            if start <= midpoint < end and word.text.strip():
                shifted.append(Word(max(start, absolute.start), min(end, absolute.end), word.text))
        # Deduplicate only the repeated timed boundary context, never an arbitrary repeated phrase.
        for count in range(min(12, len(self.final_tail), len(shifted)), 0, -1):
            old, new = self.final_tail[-count:], shifted[:count]
            if (
                all(
                    normalize_token(a.text) == normalize_token(b.text)
                    for a, b in zip(old, new, strict=True)
                )
                and new[0].start <= old[-1].end + 0.2
            ):
                shifted = shifted[count:]
                break
        agreed = 0
        for a, b in zip(state.words, shifted):
            if normalize_token(a.text) != normalize_token(b.text):
                break
            agreed += 1
        if failed:
            shifted = state.words
        text = render_words(shifted)
        if (
            not failed
            and not window.final
            and text == render_words(state.words)
            and not state.failed
        ):
            return None
        state.revision += 1
        state.words, state.failed = shifted, failed
        state.final = window.final and not failed
        if state.final:
            self.final_tail = shifted[-12:] or self.final_tail
        result = Revision(
            window.utterance_id,
            state.revision,
            "failed" if failed else "final" if state.final else "provisional",
            start,
            end,
            text[:4000],
            agreed,
            window.reason,
        )
        # Only recent finalized IDs need replay protection; windows cannot refer to older IDs.
        if len(self.states) > 64:
            for key in list(self.states):
                if key != window.utterance_id and self.states[key].final:
                    del self.states[key]
                    break
        return result
