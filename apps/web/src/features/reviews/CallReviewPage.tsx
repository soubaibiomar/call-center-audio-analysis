import {
    useCallback,
    useEffect,
    useRef,
    useState,
    type FormEvent,
} from "react";
import { Link, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useSession } from "../../app/auth";
import { ApiError, getResource, sendResource } from "../../lib/api/client";
import type {
    AnnotationDataset,
    CallEnrollment,
    CallReviewView,
    CorrectionPayload,
    DecisionInput,
    ReviewEventView,
} from "../../lib/api/generated";
import { useApiQuery, validateResource } from "../../lib/api/queries";
import { AudioPlayer } from "../calls/AudioPlayer";
import {
    Heading,
    Pending,
    QueryProblem,
    safeSeek,
    timeLabel,
} from "../workspace/shared";
import "./reviews.css";

export function CallReviewPage() {
    const { callId = "" } = useParams();
    const { identity } = useSession();
    const valid = /^[0-9a-f-]{36}$/i.test(callId);
    const reviewer = ["supervisor", "admin"].includes(
        identity.data?.role ?? "",
    );
    const query = useApiQuery<CallReviewView>(
        `/api/v1/calls/${callId}/review`,
        "CallReviewView",
        valid && reviewer,
        undefined,
        true,
    );
    if (!valid)
        return (
            <Heading title="Invalid review address">
                Choose a call from the call library.
            </Heading>
        );
    if (!reviewer)
        return (
            <section className="panel summary-panel">
                <h1>Permission required</h1>
                <p>
                    Transcript review is available to supervisors and
                    administrators.
                </p>
                <Link to="/calls">Back to calls</Link>
            </section>
        );
    if (query.isError) {
        if (
            query.error instanceof ApiError &&
            query.error.status === 404 &&
            identity.data?.role === "admin"
        )
            return (
                <Enrollment
                    callId={callId}
                    onDone={() => {
                        void query.refetch();
                    }}
                />
            );
        return <QueryProblem error={query.error} retry={query.refetch} />;
    }
    if (!query.data) return <Pending />;
    return (
        <Editor
            key={query.data.id}
            initial={query.data}
            refresh={query.refetch}
        />
    );
}

function Enrollment({
    callId,
    onDone,
}: {
    callId: string;
    onDone: () => void;
}) {
    const { accessToken } = useSession();
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);
    async function enroll(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        setBusy(true);
        setError("");
        try {
            const file = form.get("audio");
            if (
                !(file instanceof File) ||
                !file.size ||
                file.size > 25 * 1024 * 1024 ||
                !/\.(wav|mp3)$/i.test(file.name)
            )
                throw new Error("Select a WAV or MP3 recording up to 25 MB.");
            const digest = await hashFile(file);
            const data: CallEnrollment = {
                partition:
                    form.get("partition") === "evaluation"
                        ? "evaluation"
                        : "train",
                audio_sha256: digest,
                conversation_key: String(form.get("conversation")),
                speaker_keys: String(form.get("speakers"))
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                source_attestation: String(form.get("attestation")),
                source_attested: true,
                consent_to_train: form.get("consent") === "on",
                consent_evidence: String(form.get("permission")),
            };
            await sendResource(
                `/api/v1/calls/${callId}/reviews`,
                accessToken,
                "POST",
                data,
            );
            onDone();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Registration failed.");
        } finally {
            setBusy(false);
        }
    }
    return (
        <>
            <Heading title="Register review evidence">
                An administrator registers the source and permissions before
                correction begins.
            </Heading>
            <section className="panel summary-panel review-form">
                <h2>Source and permission record</h2>
                <p>
                    Local audio is hashed in your browser. Only its checksum is
                    sent. Your attestation links it to this call; a checksum
                    alone cannot prove provenance.
                </p>
                <form
                    onSubmit={(e) => {
                        void enroll(e);
                    }}
                >
                    <label>
                        Source recording
                        <input
                            name="audio"
                            type="file"
                            accept=".wav,.mp3"
                            required
                        />
                    </label>
                    <label>
                        Conversation reference
                        <input name="conversation" required maxLength={128} />
                    </label>
                    <label>
                        Speaker references, separated by commas
                        <input name="speakers" required maxLength={2000} />
                    </label>
                    <label>
                        Dataset partition
                        <select name="partition">
                            <option value="train">Training candidate</option>
                            <option value="evaluation">
                                Held-out evaluation
                            </option>
                        </select>
                    </label>
                    <label>
                        Source attestation
                        <textarea
                            name="attestation"
                            required
                            minLength={10}
                            maxLength={500}
                        />
                    </label>
                    <label>
                        Permission evidence
                        <input name="permission" required maxLength={300} />
                    </label>
                    <label className="check-label">
                        <input name="consent" type="checkbox" />
                        Documented permission allows training
                    </label>
                    <label className="check-label">
                        <input type="checkbox" required />I verified this source
                        belongs to this call and supplied stable grouping
                        references.
                    </label>
                    <button className="button" disabled={busy}>
                        Register source
                    </button>
                </form>
                {error && (
                    <p role="alert" className="error-message">
                        {error}
                    </p>
                )}
            </section>
        </>
    );
}

export async function hashFile(file: File): Promise<string> {
    const bytes = await crypto.subtle.digest(
        "SHA-256",
        await file.arrayBuffer(),
    );
    return Array.from(new Uint8Array(bytes), (b) =>
        b.toString(16).padStart(2, "0"),
    ).join("");
}

function Editor({
    initial,
    refresh,
}: {
    initial: CallReviewView;
    refresh: () => unknown;
}) {
    const { accessToken, identity } = useSession();
    const client = useQueryClient();
    const [record, setRecord] = useState(initial);
    const [payload, setPayload] = useState<CorrectionPayload>(
        structuredClone(initial.payload),
    );
    const [dirty, setDirty] = useState(false);
    const [duration, setDuration] = useState(0);
    const hashSequence = useRef(0);
    const [digest, setDigest] = useState("");
    const [ready, setReady] = useState(false);
    const [heard, setHeard] = useState(false);
    const [reason, setReason] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [events, setEvents] = useState<ReviewEventView[]>([]);
    const [exported, setExported] = useState<AnnotationDataset | null>(null);
    const audio = useRef<HTMLAudioElement>(null);
    const sequence = useRef(0);
    const admin = identity.data?.role === "admin";
    function chooseFile(file: File | null) {
        const current = ++hashSequence.current;
        setDigest("");
        setHeard(false);
        if (file)
            void hashFile(file)
                .then((d) => {
                    if (current === hashSequence.current) setDigest(d);
                })
                .catch(() => {
                    if (current === hashSequence.current)
                        setError("Cannot verify this file.");
                });
    }
    const mediaReady = useCallback((value: boolean) => {
        setReady(value);
        setDuration(value ? (audio.current?.duration ?? 0) : 0);
    }, []);
    useEffect(
        () => () => {
            sequence.current += 1;
        },
        [],
    );
    const matches =
        ready &&
        digest === record.source_audio_sha256 &&
        Math.abs(duration - record.original.duration_seconds) <= 0.25;
    const independent = ![record.author_id, record.submitter_id].includes(
        identity.data?.user_id ?? "",
    );
    function changed(value: CorrectionPayload) {
        setPayload(value);
        setDirty(true);
        setExported(null);
    }
    function seek(seconds: number) {
        const target = safeSeek(seconds, audio.current?.duration ?? 0);
        if (target !== null && audio.current) {
            audio.current.currentTime = target;
            setNotice(`Playback moved to ${timeLabel(target)}.`);
        }
    }
    async function run(work: () => Promise<void>) {
        const current = ++sequence.current;
        setBusy(true);
        setError("");
        setNotice("");
        try {
            await work();
        } catch (e) {
            if (current === sequence.current)
                setError(e instanceof Error ? e.message : "Action failed.");
        } finally {
            if (current === sequence.current) setBusy(false);
        }
    }
    async function write(
        path: string,
        method: "POST" | "PATCH",
        body: unknown,
    ) {
        const updated = validateResource<CallReviewView>(
            "CallReviewView",
            await sendResource(path, accessToken, method, body),
        );
        setRecord(updated);
        setPayload(structuredClone(updated.payload));
        setDirty(false);
        setHeard(false);
        setExported(null);
        setEvents([]);
        void client.invalidateQueries({
            queryKey: ["workspace"],
            refetchType: "none",
        });
        setNotice(
            `Review ${updated.state}. Revision ${updated.revision} saved.`,
        );
    }
    function decision(action: DecisionInput["action"]) {
        void run(async () => {
            await write(`/api/v1/call-reviews/${record.id}/decisions`, "POST", {
                action,
                expected_revision: record.revision,
                rationale: reason,
                listened_to_audio: true,
                observed_audio_sha256: digest,
                observed_duration_seconds: audio.current?.duration ?? 0,
            } satisfies DecisionInput);
            setReason("");
        });
    }
    async function reload() {
        await run(async () => {
            const updated = validateResource<CallReviewView>(
                "CallReviewView",
                await getResource(
                    `/api/v1/calls/${record.call_id}/review`,
                    accessToken,
                ),
            );
            setRecord(updated);
            setPayload(structuredClone(updated.payload));
            setDirty(false);
            setHeard(false);
            setExported(null);
            setEvents([]);
            setNotice(
                "Latest revision loaded. Reapply any unsaved corrections.",
            );
        });
    }
    return (
        <>
            <Heading title="Human transcript & QA review">
                Listen, correct and submit for independent approval. Original
                model predictions remain preserved.
            </Heading>
            <div className="call-heading">
                <Link to={`/calls/${record.call_id}`} className="text-button">
                    Back to call analysis
                </Link>
                <span
                    className={`pill ${record.state === "approved" ? "success" : "caution"}`}
                >
                    {record.state}
                </span>
                <span>
                    Revision {record.revision} · {record.partition}
                </span>
                <button
                    className="secondary-button"
                    disabled={busy}
                    onClick={() => {
                        void reload();
                    }}
                >
                    Refresh review (discard unsaved)
                </button>
            </div>
            {error && (
                <p role="alert" className="error-message">
                    {error}
                </p>
            )}
            <output aria-live="polite">{notice}</output>
            <div className="review-metrics">
                <section className="panel summary-panel">
                    <p className="eyebrow">ORIGINAL QA</p>
                    <strong>
                        {record.original.qa_scores.overall_score.toFixed(2)} / 5
                    </strong>
                    <p>Model prediction, preserved</p>
                </section>
                <section className="panel summary-panel">
                    <p className="eyebrow">CORRECTION</p>
                    <strong>
                        {payload.qa_override?.score ?? "Unchanged"}
                        {payload.qa_override ? " / 5" : ""}
                    </strong>
                    <p>{dirty ? "Unsaved changes" : "Saved revision"}</p>
                </section>
                <section className="panel summary-panel">
                    <p className="eyebrow">TRAINING CANDIDATE</p>
                    <strong>
                        {record.eligible_for_training ? "Eligible" : "Excluded"}
                    </strong>
                    <p>
                        Permission{" "}
                        {record.consent_to_train ? "recorded" : "withheld"} ·
                        uncertainty checks apply
                    </p>
                </section>
            </div>
            <AudioPlayer
                audioRef={audio}
                onReady={mediaReady}
                onFileSelected={chooseFile}
                registeredSource
                segments={record.original.transcription.segments}
            />
            <output className="notice">
                {matches
                    ? "Checksum and duration match the registered source."
                    : "Select the registered recording to enable review decisions."}
            </output>
            <section className="panel summary-panel">
                <h2>Registered source</h2>
                <p>{record.source_attestation}</p>
                <p className="field-hint review-hash">
                    SHA-256 {record.source_audio_sha256}
                </p>
            </section>
            <section className="panel transcript-panel">
                <div className="section-title">
                    <div>
                        <p className="eyebrow">TIMESTAMPED CORRECTIONS</p>
                        <h2 id="transcript-heading">Transcript review</h2>
                    </div>
                    <span className="pill neutral">
                        {payload.segments.length} segments
                    </span>
                </div>
                <p>
                    Timing stays attached to the original prediction. Select a
                    timestamp to listen.
                </p>
                <ol className="review-segments">
                    {payload.segments.map((segment, index) => {
                        const raw =
                            record.original.transcription.segments[
                                segment.segment_index
                            ];
                        if (!raw) return null;
                        return (
                            <li key={segment.segment_index}>
                                <div className="section-title">
                                    <button
                                        className="timestamp"
                                        disabled={!ready}
                                        onClick={() => seek(raw.start_time)}
                                    >
                                        {timeLabel(raw.start_time)}–
                                        {timeLabel(raw.end_time)}
                                    </button>
                                    <span className="pill neutral">
                                        Confidence{" "}
                                        {raw.confidence == null
                                            ? "unavailable"
                                            : `${Math.round(raw.confidence * 100)}%`}
                                    </span>
                                </div>
                                <p className="field-hint">
                                    Original ·{" "}
                                    {raw.speaker_role ||
                                        raw.speaker ||
                                        "Unknown"}
                                    : {raw.text}
                                </p>
                                <label>
                                    Corrected text {index + 1}
                                    <textarea
                                        aria-label={`Corrected text ${index + 1}`}
                                        maxLength={4000}
                                        value={segment.text}
                                        onChange={(e) =>
                                            changed({
                                                ...payload,
                                                segments: payload.segments.map(
                                                    (s, i) =>
                                                        i === index
                                                            ? {
                                                                  ...s,
                                                                  text: e.target
                                                                      .value,
                                                              }
                                                            : s,
                                                ),
                                            })
                                        }
                                    />
                                </label>
                                <div className="review-fields">
                                    <label>
                                        Speaker {index + 1}
                                        <select
                                            aria-label={`Speaker ${index + 1}`}
                                            value={segment.speaker_role}
                                            onChange={(e) =>
                                                changed({
                                                    ...payload,
                                                    segments:
                                                        payload.segments.map(
                                                            (s, i) =>
                                                                i === index
                                                                    ? {
                                                                          ...s,
                                                                          speaker_role:
                                                                              e
                                                                                  .target
                                                                                  .value as typeof s.speaker_role,
                                                                      }
                                                                    : s,
                                                        ),
                                                })
                                            }
                                        >
                                            <option>Agent</option>
                                            <option>Customer</option>
                                            <option>Unknown</option>
                                        </select>
                                    </label>
                                    <label className="check-label">
                                        <input
                                            type="checkbox"
                                            checked={segment.uncertain}
                                            onChange={(e) =>
                                                changed({
                                                    ...payload,
                                                    segments:
                                                        payload.segments.map(
                                                            (s, i) =>
                                                                i === index
                                                                    ? {
                                                                          ...s,
                                                                          uncertain:
                                                                              e
                                                                                  .target
                                                                                  .checked,
                                                                      }
                                                                    : s,
                                                        ),
                                                })
                                            }
                                        />
                                        Uncertain segment {index + 1}
                                    </label>
                                </div>
                            </li>
                        );
                    })}
                </ol>
            </section>
            <section className="panel summary-panel review-form">
                <h2>QA score correction</h2>
                <label className="check-label">
                    <input
                        type="checkbox"
                        checked={!!payload.qa_override}
                        onChange={(e) =>
                            changed({
                                ...payload,
                                qa_override: e.target.checked
                                    ? {
                                          score: record.original.qa_scores
                                              .overall_score,
                                          rationale: "",
                                          audio_start: 0,
                                          audio_end: Math.min(
                                              1,
                                              record.original.duration_seconds,
                                          ),
                                      }
                                    : null,
                            })
                        }
                    />
                    Override overall QA score
                </label>
                {payload.qa_override && (
                    <>
                        <label>
                            Corrected QA score
                            <input
                                type="number"
                                min={1}
                                max={5}
                                step={0.1}
                                value={payload.qa_override.score}
                                onChange={(e) =>
                                    changed({
                                        ...payload,
                                        qa_override: {
                                            ...payload.qa_override!,
                                            score: Number(e.target.value),
                                        },
                                    })
                                }
                            />
                        </label>
                        <label>
                            QA rationale
                            <textarea
                                aria-label="QA rationale"
                                minLength={10}
                                maxLength={2000}
                                value={payload.qa_override.rationale}
                                onChange={(e) =>
                                    changed({
                                        ...payload,
                                        qa_override: {
                                            ...payload.qa_override!,
                                            rationale: e.target.value,
                                        },
                                    })
                                }
                            />
                        </label>
                        <div className="review-fields">
                            <label>
                                Evidence start (seconds)
                                <input
                                    type="number"
                                    min={0}
                                    max={record.original.duration_seconds}
                                    step={0.01}
                                    value={payload.qa_override.audio_start}
                                    onChange={(e) =>
                                        changed({
                                            ...payload,
                                            qa_override: {
                                                ...payload.qa_override!,
                                                audio_start: Number(
                                                    e.target.value,
                                                ),
                                            },
                                        })
                                    }
                                />
                            </label>
                            <label>
                                Evidence end (seconds)
                                <input
                                    type="number"
                                    min={0}
                                    max={record.original.duration_seconds}
                                    step={0.01}
                                    value={payload.qa_override.audio_end}
                                    onChange={(e) =>
                                        changed({
                                            ...payload,
                                            qa_override: {
                                                ...payload.qa_override!,
                                                audio_end: Number(
                                                    e.target.value,
                                                ),
                                            },
                                        })
                                    }
                                />
                            </label>
                        </div>
                        <button
                            className="secondary-button"
                            disabled={!ready}
                            onClick={() =>
                                seek(payload.qa_override!.audio_start)
                            }
                        >
                            Listen to QA evidence
                        </button>
                    </>
                )}
            </section>
            <section className="panel summary-panel review-form">
                <h2>Review decision</h2>
                <p>
                    Save corrections before submitting. Approval or rejection
                    requires a different reviewer. Editing a saved review resets
                    its approval.
                </p>
                <button
                    className="button"
                    disabled={busy || !dirty}
                    onClick={() => {
                        void run(() =>
                            write(
                                `/api/v1/call-reviews/${record.id}`,
                                "PATCH",
                                {
                                    ...payload,
                                    expected_revision: record.revision,
                                },
                            ),
                        );
                    }}
                >
                    Save corrections
                </button>
                <label>
                    Decision rationale
                    <textarea
                        aria-label="Decision rationale"
                        minLength={10}
                        maxLength={2000}
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                    />
                </label>
                <label className="check-label">
                    <input
                        type="checkbox"
                        checked={heard}
                        disabled={!matches}
                        onChange={(e) => setHeard(e.target.checked)}
                    />
                    I listened to the relevant audio and checked this saved
                    revision.
                </label>
                <div className="call-heading">
                    <button
                        className="button"
                        disabled={
                            busy ||
                            dirty ||
                            !matches ||
                            !heard ||
                            reason.trim().length < 10 ||
                            record.state !== "draft" ||
                            record.author_id !== identity.data?.user_id
                        }
                        onClick={() => decision("submit")}
                    >
                        Submit for approval
                    </button>
                    <button
                        className="button"
                        disabled={
                            busy ||
                            dirty ||
                            !matches ||
                            !heard ||
                            reason.trim().length < 10 ||
                            record.state !== "submitted" ||
                            !independent
                        }
                        onClick={() => decision("approve")}
                    >
                        Approve review
                    </button>
                    <button
                        className="secondary-button"
                        disabled={
                            busy ||
                            dirty ||
                            !matches ||
                            !heard ||
                            reason.trim().length < 10 ||
                            record.state !== "submitted" ||
                            !independent
                        }
                        onClick={() => decision("reject")}
                    >
                        Reject review
                    </button>
                </div>
                <p className="field-hint">
                    Editor: {record.author_id ?? "None"} · Approver:{" "}
                    {record.approver_id ?? "None"}
                </p>
            </section>
            <section className="panel summary-panel review-form">
                <h2>Audit trail</h2>
                <button
                    className="secondary-button"
                    disabled={busy}
                    onClick={() => {
                        void run(async () => {
                            const data = await getResource<unknown>(
                                `/api/v1/call-reviews/${record.id}/history`,
                                accessToken,
                            );
                            if (!Array.isArray(data)) throw new ApiError(502);
                            setEvents(
                                data.map((e) =>
                                    validateResource<ReviewEventView>(
                                        "ReviewEventView",
                                        e,
                                    ),
                                ),
                            );
                        });
                    }}
                >
                    Load audit history
                </button>
                <ol>
                    {events.map((e) => (
                        <li key={e.id}>
                            <strong>{e.action}</strong> · revision {e.revision}{" "}
                            · {e.actor_id} ·{" "}
                            {new Date(e.created_at).toLocaleString()}
                            <p className="field-hint review-hash">
                                Snapshot SHA-256 {e.payload_sha256}
                            </p>
                        </li>
                    ))}
                </ol>
            </section>
            {admin && (
                <section className="panel summary-panel review-form">
                    <h2>Dataset permissions & export</h2>
                    <p>
                        Only independently approved, certain training candidates
                        with current permission and unexpired sources are
                        included. Downloaded exports must be revalidated before
                        use.
                    </p>
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            const data = new FormData(e.currentTarget);
                            void run(() =>
                                write(
                                    `/api/v1/call-reviews/${record.id}/consent`,
                                    "PATCH",
                                    {
                                        expected_revision: record.revision,
                                        consent_to_train:
                                            data.get("allow") === "on",
                                        consent_evidence: String(
                                            data.get("evidence"),
                                        ),
                                    },
                                ),
                            );
                        }}
                    >
                        <label className="check-label">
                            <input
                                name="allow"
                                type="checkbox"
                                defaultChecked={record.consent_to_train}
                                key={record.revision}
                            />
                            Training permission
                        </label>
                        <label>
                            Updated permission evidence
                            <input name="evidence" required maxLength={300} />
                        </label>
                        <button className="secondary-button" disabled={busy}>
                            Save permission
                        </button>
                    </form>
                    <button
                        className="button"
                        disabled={busy}
                        onClick={() => {
                            void run(async () => {
                                setExported(
                                    validateResource<AnnotationDataset>(
                                        "AnnotationDataset",
                                        await getResource(
                                            "/api/v1/call-review-dataset",
                                            accessToken,
                                        ),
                                    ),
                                );
                            });
                        }}
                    >
                        Preview approved export
                    </button>
                    {exported && (
                        <div>
                            <p>
                                {exported.items.length} calls ·{" "}
                                {exported.approved_segments} approved segments
                                {exported.truncated
                                    ? " · candidate limit reached"
                                    : ""}
                            </p>
                            <p className="review-hash field-hint">
                                Manifest SHA-256 {exported.fingerprint}
                            </p>
                            <button
                                className="secondary-button"
                                onClick={() => {
                                    const url = URL.createObjectURL(
                                        new Blob(
                                            [JSON.stringify(exported, null, 2)],
                                            { type: "application/json" },
                                        ),
                                    );
                                    const a = document.createElement("a");
                                    a.href = url;
                                    a.download =
                                        "approved-call-annotations.json";
                                    a.click();
                                    setTimeout(
                                        () => URL.revokeObjectURL(url),
                                        1000,
                                    );
                                }}
                            >
                                Download annotation manifest
                            </button>
                        </div>
                    )}
                    <details>
                        <summary>
                            Erase annotation and its audit snapshots
                        </summary>
                        <p>
                            Removes this correction, retained transcript copies
                            and review history. The source prediction remains
                            under its call retention policy.
                        </p>
                        <button
                            className="secondary-button"
                            disabled={busy}
                            onClick={() => {
                                void run(async () => {
                                    await sendResource(
                                        `/api/v1/call-reviews/${record.id}?expected_revision=${record.revision}`,
                                        accessToken,
                                        "DELETE",
                                    );
                                    refresh();
                                });
                            }}
                        >
                            Erase this annotation
                        </button>
                    </details>
                </section>
            )}
        </>
    );
}
