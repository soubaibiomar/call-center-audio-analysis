import { expect, it } from "vitest";
import { applyTranscript, type TranscriptRow } from "./transcript";
import type { LiveEvent, TranscriptRevision } from "../../lib/api/generated";

const id = "11111111-1111-4111-8111-111111111111";
const user = "22222222-2222-4222-8222-222222222222";
function event(
    revision: number,
    state: TranscriptRevision["state"] = "provisional",
    text = "transcrip-",
): LiveEvent {
    return {
        type: "transcript",
        sender_user_id: user,
        consent_revision: 7,
        transcript: {
            utterance_id: id,
            revision,
            state,
            text,
            start_seconds: 0,
            end_seconds: 2,
            agreed_prefix_words: 0,
            reason: "partial",
            timing: "word",
            window_start_seconds: 0,
            window_end_seconds: 2,
            ready_to_event_ms: 3,
            inference_ms: 2,
        },
    };
}
it("replaces partial words and punctuation in one keyed row", () => {
    const a = applyTranscript([], event(1), 7);
    const b = applyTranscript(a, event(2, "provisional", "transcription."), 7);
    expect(b).toHaveLength(1);
    expect(b[0]?.text).toBe("transcription.");
    expect(b[0]?.utterance_id).toBe(a[0]?.utterance_id);
});
it("rejects duplicate and out-of-order revisions", () => {
    const rows = applyTranscript([], event(3), 7);
    expect(applyTranscript(rows, event(2), 7)).toBe(rows);
    expect(applyTranscript(rows, event(3), 7)).toBe(rows);
});
it("keeps final rows immutable", () => {
    const rows = applyTranscript([], event(2, "final", "Finished."), 7);
    expect(applyTranscript(rows, event(4, "provisional", "Changed."), 7)).toBe(
        rows,
    );
});
it("does not mix revoked epochs or empty socket events into transcript", () => {
    const rows = applyTranscript([], event(1), 7);
    expect(applyTranscript(rows, event(2), 8)).toBe(rows);
    expect(applyTranscript(rows, event(2), null)).toBe(rows);
    expect(applyTranscript(rows, { type: "pong" }, 7)).toBe(rows);
});
it("recovers a failed row in place with a newer hypothesis", () => {
    let rows = applyTranscript([], event(1), 7);
    rows = applyTranscript(rows, event(2, "failed"), 7);
    rows = applyTranscript(rows, event(3, "final", "Recovered."), 7);
    expect(rows).toHaveLength(1);
    expect(rows[0]?.state).toBe("final");
});
it("keeps identical utterance IDs from distinct microphone users separate", () => {
    const rows = applyTranscript([], event(1), 7);
    const second = { ...event(1), sender_user_id: id };
    expect(applyTranscript(rows, second, 7)).toHaveLength(2);
});
it("bounds recent rows without treating repeated text as duplicate speech", () => {
    let rows: TranscriptRow[] = [];
    for (let i = 0; i < 105; i++) {
        const next = event(1, "final", "No.");
        next.transcript!.utterance_id = String(i).padStart(36, "0");
        rows = applyTranscript(rows, next, 7);
    }
    expect(rows).toHaveLength(100);
    expect(rows.every((row) => row.text === "No.")).toBe(true);
});
