"""Local synthetic/permissioned PCM replay; reports observations, never model improvement."""

import argparse
import asyncio
import hashlib
import json
import math
import statistics
import time
import wave
from pathlib import Path
from uuid import UUID, uuid4

from ml.asr.incremental import Reconciler, SpeechWindows
from services.api.auth import Principal
from services.streaming.asr import LocalWhisper, recognize_words
from services.streaming.broker import LiveBroker
from services.streaming.contracts import LiveConsent, LivePeer
from services.streaming.settings import LiveSettings
from src.security.pii_redactor import redact_pii


def percentiles(values: list[float]) -> dict[str, float | int | None]:
    ordered = sorted(values)
    return {
        "n": len(values),
        "p50": statistics.median(values) if values else None,
        "p95": ordered[math.ceil(0.95 * len(ordered)) - 1] if values else None,
    }


async def load(adapter: LocalWhisper, pcm: bytes, streams: int, seconds: int) -> dict[str, object]:
    broker = LiveBroker(LiveSettings(enabled=True, origins=("http://127.0.0.1:8790",)), adapter)
    identities = []
    rooms = []
    observed = []
    for _ in range((streams + 1) // 2):
        users = [Principal("synthetic-load", str(uuid4()), "agent") for _ in range(2)]
        created = broker.create(
            users[0],
            *(LivePeer(user_id=UUID(u.user_id), display_name="Synthetic load") for u in users),
        )
        room = broker.room(str(created.id), users[0])
        rooms.append(room)
        for identity in users:
            ticket = broker.issue(room, identity, time.time() + 600)
            broker.attach(room.id, ticket.ticket)
            broker.consent(room, identity, LiveConsent(microphone=True, analysis=True))
            broker.connection(room, identity, "connected")
            identities.append((identity, room))
        for p in room.participants.values():
            while not p.queue.empty():
                p.queue.get_nowait()
    accepted = rejected = peak_queue = peak_buffer = 0
    started = time.perf_counter()
    for i in range(seconds):
        for identity, room in identities[:streams]:
            if not broker.allowed(room):
                continue
            try:
                broker.audio(
                    room, identity, pcm[i * 32000 : (i + 1) * 32000], i, i * 16000, room.revision
                )
                accepted += 1
            except Exception as error:
                if getattr(error, "status_code", None) != 429:
                    raise
                rejected += 1
            peak_queue = max(peak_queue, broker.work.qsize())
            peak_buffer = max(
                peak_buffer, sum(len(p.buffer) for r in rooms for p in r.participants.values())
            )
            await asyncio.sleep(0)
        await asyncio.sleep(1)
        for room in rooms:
            queue = next(iter(room.participants.values())).queue
            while queue is not None and not queue.empty():
                event = queue.get_nowait()
                if event.transcript:
                    observed.append(event.transcript.model_dump(mode="json"))
    for identity, room in identities[:streams]:
        if broker.allowed(room):
            try:
                broker.flush(room, identity, room.revision)
            except Exception as error:
                if getattr(error, "status_code", None) != 429:
                    raise
                rejected += 1
    if broker.worker is not None:
        await broker.worker
    for room in rooms:
        queue = next(iter(room.participants.values())).queue
        while queue is not None and not queue.empty():
            event = queue.get_nowait()
            if event.transcript:
                observed.append(event.transcript.model_dump(mode="json"))
    paused = sum(not broker.allowed(room) for room in rooms)
    coalesced = broker.coalesced
    await broker.close()
    return dict(
        streams=streams,
        seconds=seconds,
        wall_seconds=time.perf_counter() - started,
        accepted_frames=accepted,
        rejected_or_backpressured=rejected,
        paused_rooms=paused,
        coalesced=coalesced,
        peak_pending=peak_queue,
        peak_track_buffer_bytes=peak_buffer,
        partial_ready_to_event_ms=percentiles(
            [r["ready_to_event_ms"] for r in observed if r["state"] == "provisional"]
        ),
        revisions=observed,
        all_rooms_cleared=not broker.rooms and not broker.tickets,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--model-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=12, choices=range(4, 21))
    args = parser.parse_args()
    with wave.open(str(args.audio), "rb") as source:
        if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, 16000):
            raise ValueError("Expected mono 16 kHz PCM16 WAV")
        pcm = source.readframes(args.seconds * 16000)
    pcm = pcm.ljust(args.seconds * 32000, b"\0")
    adapter = LocalWhisper(args.model_file.read_text(encoding="utf-8").strip())
    adapter.transcribe_words(pcm[:64000])  # warm-up is excluded from the following timings.
    baseline = []
    for start in range(0, len(pcm), 128000):
        data = pcm[start : start + 128000]
        before = time.perf_counter()
        spans = adapter.transcribe(data)
        elapsed = time.perf_counter() - before
        baseline.append(
            dict(
                start_seconds=start / 32000,
                audio_seconds=len(data) / 32000,
                inference_seconds=elapsed,
                rtf=elapsed / (len(data) / 32000),
                text=" ".join(s.text for s in spans),
            )
        )
    track = SpeechWindows()
    reconcile = Reconciler()
    calls = []
    revisions = []
    windows = []
    for start in range(0, len(pcm), 32000):
        windows.extend(track.push(pcm[start : start + 32000], start // 2))
    tail = track.flush()
    if tail:
        windows.append(tail)
    for window in windows:
        before = time.perf_counter()
        words, timing = recognize_words(adapter, window.pcm)
        elapsed = time.perf_counter() - before
        revision = reconcile.apply(window, words)
        calls.append(
            dict(
                audio_seconds=len(window.pcm) / 32000,
                inference_seconds=elapsed,
                rtf=elapsed / (len(window.pcm) / 32000),
                final=window.final,
            )
        )
        if revision:
            revisions.append(
                dict(
                    id=revision.utterance_id,
                    revision=revision.revision,
                    state=revision.state,
                    text=redact_pii(revision.text).redacted_text,
                    start=revision.start,
                    end=revision.end,
                    reason=revision.reason,
                    timing=timing,
                )
            )
    result = dict(
        source="local synthetic/permissioned WAV; no accuracy ground truth",
        source_sha256=hashlib.sha256(args.audio.read_bytes()).hexdigest(),
        model_revision=adapter.path.name,
        cpu_threads=4,
        compute_type="int8",
        seconds=args.seconds,
        warmup_excluded=True,
        baseline_4s=baseline,
        incremental_calls=calls,
        incremental_revisions=revisions,
        incremental_rtf=percentiles([c["rtf"] for c in calls]),
        note=(
            "Whisper is chunked, not natively streaming. Load replay paces one-second "
            "frames through the actual broker; no WebRTC/network timing in these load cases."
        ),
    )
    result["load"] = [asyncio.run(load(adapter, pcm, n, args.seconds)) for n in [1, 2, 4]]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Measured baseline, incremental decoding and paced 1/2/4-source load; evidence saved.")


if __name__ == "__main__":
    main()
