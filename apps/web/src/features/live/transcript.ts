import type { LiveEvent, TranscriptRevision } from "../../lib/api/generated";

export type TranscriptRow = TranscriptRevision & {
    sender_user_id: string;
    consent_revision: number;
};

export function applyTranscript(
    rows: TranscriptRow[],
    event: LiveEvent,
    epoch: number | null,
): TranscriptRow[] {
    if (
        event.type !== "transcript" ||
        !event.transcript ||
        !event.sender_user_id ||
        epoch === null ||
        event.consent_revision !== epoch
    )
        return rows;
    const candidate: TranscriptRow = {
        ...event.transcript,
        sender_user_id: event.sender_user_id,
        consent_revision: epoch,
    };
    const index = rows.findIndex(
        (row) =>
            row.utterance_id === candidate.utterance_id &&
            row.sender_user_id === candidate.sender_user_id,
    );
    const previous = rows[index];
    if (
        previous &&
        (previous.state === "final" || previous.revision >= candidate.revision)
    )
        return rows;
    const current = rows.filter((row) => row.consent_revision === epoch);
    const target = current.findIndex(
        (row) =>
            row.utterance_id === candidate.utterance_id &&
            row.sender_user_id === candidate.sender_user_id,
    );
    if (target < 0) return [...current, candidate].slice(-100);
    return current.map((row, i) => (i === target ? candidate : row));
}
