import { useEffect, useRef, useState } from "react";
import { useSession } from "../../app/auth";
import type {
    LiveConfig,
    LivePeers,
    LiveSessions,
    LiveSessionView,
} from "../../lib/api/generated";
import { sendResource } from "../../lib/api/client";
import { useApiQuery } from "../../lib/api/queries";
import { Heading, Pending, QueryProblem, timeLabel } from "../workspace/shared";
import { BatchMonitor } from "./BatchMonitor";
import { BrowserCall, liveError, type CallUpdate } from "./transport";
import { applyTranscript, type TranscriptRow } from "./transcript";
import "./live.css";

export function LivePage() {
    const config = useApiQuery<LiveConfig>("/api/v1/live/config", "LiveConfig");
    return (
        <>
            <Heading title="Live monitoring">
                Consented browser-to-browser calling and authorized local audio
                analysis.
            </Heading>
            {config.isError ? (
                <QueryProblem error={config.error} retry={config.refetch} />
            ) : !config.data ? (
                <Pending />
            ) : config.data.enabled ? (
                <BrowserCalling config={config.data} />
            ) : (
                <section className="panel summary-panel">
                    <span className="pill neutral">
                        No live transport available
                    </span>
                    <h2>Browser calling is disabled</h2>
                    <p>
                        An administrator must enable the single-worker demo and
                        its allowed origins. Batch monitoring remains available
                        below.
                    </p>
                </section>
            )}
            <BatchMonitor />
        </>
    );
}

function BrowserCalling({ config }: { config: LiveConfig }) {
    const { accessToken, identity } = useSession();
    const peers = useApiQuery<LivePeers>("/api/v1/live/peers", "LivePeers");
    const invitations = useApiQuery<LiveSessions>(
        "/api/v1/live/sessions",
        "LiveSessions",
        true,
        3000,
    );
    const [peerId, setPeerId] = useState("");
    const [micConsent, setMicConsent] = useState(false);
    const [analysis, setAnalysis] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [view, setView] = useState<CallUpdate>({
        connection: "idle",
        receivedSamples: 0,
    });
    const [transcript, setTranscript] = useState<TranscriptRow[]>([]);
    const epoch = useRef<number | null>(null);
    const controller = useRef<BrowserCall | null>(null);
    const remote = useRef<HTMLAudioElement>(null);
    useEffect(
        () => () => {
            void controller.current?.stop(
                "Workspace closed. Microphone released.",
            );
        },
        [],
    );
    const room = view.session ?? invitations.data?.items[0];
    const active = view.connection !== "idle" && view.connection !== "ended";
    const me = view.session?.participants.find(
        (p) => p.user_id === identity.data?.user_id,
    );
    const stats = view.stats;
    async function create() {
        if (!peerId) return;
        setBusy(true);
        setError("");
        try {
            await sendResource("/api/v1/live/sessions", accessToken, "POST", {
                peer_user_id: peerId,
            });
            await invitations.refetch();
        } catch (e) {
            setError(liveError(e));
        } finally {
            setBusy(false);
        }
    }
    async function join(selected: LiveSessionView) {
        if (!micConsent || !remote.current || !identity.data) return;
        setBusy(true);
        setError("");
        setTranscript([]);
        const call = new BrowserCall(
            accessToken,
            identity.data.user_id,
            remote.current,
            (patch) => {
                setView((prev) => ({ ...prev, ...patch }));
                if (patch.session) {
                    epoch.current = patch.session.capture_allowed
                        ? patch.session.consent_revision
                        : null;
                    setTranscript((previous) =>
                        previous.filter(
                            (row) => row.consent_revision === epoch.current,
                        ),
                    );
                    const own = patch.session.participants.find(
                        (p) => p.user_id === identity.data?.user_id,
                    );
                    if (own) setAnalysis(own.analysis);
                }
                if (
                    (patch.session && !patch.session.capture_allowed) ||
                    patch.session === null
                )
                    setTranscript([]);
                if (patch.event)
                    setTranscript((prev) =>
                        applyTranscript(prev, patch.event!, epoch.current),
                    );
                if (patch.session === null) {
                    setMicConsent(false);
                    setAnalysis(false);
                    void invitations.refetch();
                }
            },
        );
        controller.current = call;
        setView({ connection: "requesting microphone", receivedSamples: 0 });
        try {
            await call.connect(selected, analysis);
        } catch (e) {
            setError(liveError(e));
        } finally {
            setBusy(false);
        }
    }
    async function changeAnalysis(value: boolean) {
        setAnalysis(value);
        if (active) {
            await controller.current?.setAnalysis(value);
        }
    }
    return (
        <>
            <section className="panel summary-panel live-intro">
                <div>
                    <p className="eyebrow">DIRECT BROWSER CALL · LOCAL DEMO</p>
                    <h2>A conversation with consent.</h2>
                    <p>
                        WebRTC carries peer audio. Analysis receives a separate
                        copy only after both participants allow it. No recording
                        is saved. This is not a telephone or PBX connection.
                    </p>
                </div>
                <span className="pill caution">
                    Direct connection · no TURN relay
                </span>
            </section>
            <section className="panel summary-panel live-form">
                <h2>Call setup</h2>
                {peers.isError ? (
                    <QueryProblem error={peers.error} retry={peers.refetch} />
                ) : (
                    <label>
                        Call participant
                        <select
                            aria-label="Call participant"
                            value={peerId}
                            disabled={active || busy}
                            onChange={(e) => setPeerId(e.target.value)}
                        >
                            <option value="">
                                Choose an enabled workspace member
                            </option>
                            {peers.data?.items.map((p) => (
                                <option key={p.user_id} value={p.user_id}>
                                    {p.display_name} · {p.user_id.slice(0, 8)}
                                </option>
                            ))}
                        </select>
                    </label>
                )}
                <div className="call-heading">
                    <button
                        className="button"
                        disabled={busy || active || !peerId || !!room}
                        onClick={() => {
                            void create();
                        }}
                    >
                        Create call invitation
                    </button>
                    <button
                        className="secondary-button"
                        disabled={busy}
                        onClick={() => {
                            void invitations.refetch();
                        }}
                    >
                        Refresh call invitations
                    </button>
                </div>
                {invitations.isError && (
                    <QueryProblem
                        error={invitations.error}
                        retry={invitations.refetch}
                    />
                )}
                {room && (
                    <p className="field-hint live-id">
                        Session {room.id} · expires within{" "}
                        {room.remaining_seconds} seconds
                    </p>
                )}
                {!room && (
                    <p className="muted">
                        No invitation is waiting for your account.
                    </p>
                )}
                <label className="check-label">
                    <input
                        type="checkbox"
                        checked={micConsent}
                        disabled={active}
                        onChange={(e) => setMicConsent(e.target.checked)}
                    />
                    I consent to use my microphone for this two-party call.
                </label>
                <label className="check-label">
                    <input
                        type="checkbox"
                        checked={analysis}
                        disabled={
                            !config.analysis_available ||
                            busy ||
                            (active && !me?.microphone)
                        }
                        onChange={(e) => {
                            void changeAnalysis(e.target.checked);
                        }}
                    />
                    I allow my microphone audio to be analyzed locally for this
                    call.
                </label>
                {!config.analysis_available && (
                    <p className="field-hint">
                        Local ASR is not configured. The browser call remains
                        available without analysis.
                    </p>
                )}
                <div className="call-heading">
                    <button
                        className="button"
                        disabled={busy || active || !micConsent || !room}
                        onClick={() => {
                            if (room) void join(room);
                        }}
                    >
                        Join with microphone
                    </button>
                    <button
                        className="secondary-button"
                        disabled={!active}
                        onClick={() => {
                            void controller.current?.stop();
                        }}
                    >
                        End call
                    </button>
                    <button
                        className="secondary-button"
                        disabled={
                            busy ||
                            active ||
                            !peerId ||
                            !!room ||
                            view.connection !== "ended"
                        }
                        onClick={() => {
                            void create();
                        }}
                    >
                        Reconnect with a new invitation
                    </button>
                    {room && !active && (
                        <button
                            className="secondary-button"
                            disabled={busy}
                            onClick={() => {
                                void sendResource(
                                    `/api/v1/live/sessions/${room.id}`,
                                    accessToken,
                                    "DELETE",
                                )
                                    .then(() => invitations.refetch())
                                    .catch((e) => setError(liveError(e)));
                            }}
                        >
                            Cancel invitation
                        </button>
                    )}
                </div>
                <p className="field-hint">
                    Joining requests your browser's microphone permission.
                    Ending, disconnecting or leaving this page releases the
                    microphone and clears the session. Reconnection requires
                    fresh consent.
                </p>
                {error && (
                    <p role="alert" className="error-message">
                        {error}
                    </p>
                )}
                <output aria-live="polite">{view.notice}</output>
            </section>
            <div className="live-participants">
                {view.session?.participants.map((p) => {
                    const local = p.user_id === identity.data?.user_id;
                    const level = local
                        ? stats?.localLevel
                        : stats?.remoteLevel;
                    return (
                        <section
                            className="panel summary-panel"
                            key={p.user_id}
                        >
                            <p className="eyebrow">
                                {local
                                    ? "YOUR MICROPHONE"
                                    : "OTHER PARTICIPANT"}
                            </p>
                            <h2>{p.display_name}</h2>
                            <p>
                                {p.media_state} ·{" "}
                                {p.socket_connected
                                    ? "signaling connected"
                                    : "waiting for signaling"}
                            </p>
                            <span
                                className={`pill ${level != null && level > 0.01 ? "positive" : "neutral"}`}
                            >
                                {level == null
                                    ? "Audio level not measured"
                                    : level > 0.01
                                      ? "Audio activity detected"
                                      : "Quiet audio"}
                            </span>
                            <p className="field-hint">
                                Microphone{" "}
                                {p.microphone ? "permitted" : "not permitted"} ·
                                analysis{" "}
                                {p.analysis ? "permitted" : "not permitted"}
                            </p>
                        </section>
                    );
                })}
            </div>
            <section className="panel summary-panel">
                <div className="section-title">
                    <h2>Connection & audio</h2>
                    <span
                        className="pill neutral"
                        data-testid="call-connection"
                    >
                        {view.connection}
                    </span>
                </div>
                <audio
                    ref={remote}
                    autoPlay
                    controls
                    aria-label="Remote participant audio"
                >
                    <track
                        kind="captions"
                        label="Live transcript appears below"
                    />
                </audio>
                <button
                    className="secondary-button"
                    disabled={!active}
                    onClick={() => {
                        void remote.current
                            ?.play()
                            .catch(() =>
                                setError(
                                    "Your browser has blocked speaker playback.",
                                ),
                            );
                    }}
                >
                    Enable speaker
                </button>
                <dl className="live-stats">
                    <dt>Negotiated peer codec</dt>
                    <dd data-testid="audio-codec">
                        {stats?.codec ?? "Not measured"}
                    </dd>
                    <dt>Encrypted media transport</dt>
                    <dd data-testid="dtls-state">
                        {stats?.dtlsState ?? "Not measured"}
                    </dd>
                    <dt>Received audio packets</dt>
                    <dd data-testid="received-packets">
                        {stats?.packetsReceived ?? "Not measured"}
                    </dd>
                    <dt>Lost audio packets</dt>
                    <dd data-testid="lost-packets">
                        {stats?.packetsLost ?? "Not measured"}
                    </dd>
                    <dt>Received audio bytes</dt>
                    <dd data-testid="received-bytes">
                        {stats?.bytesReceived ?? "Not measured"}
                    </dd>
                    <dt>Concealed / received samples</dt>
                    <dd data-testid="continuity">
                        {stats?.concealedSamples == null
                            ? "Not measured"
                            : `${stats.concealedSamples} / ${stats.totalSamplesReceived}`}
                    </dd>
                    <dt>Server-accepted analysis samples</dt>
                    <dd data-testid="capture-samples">
                        {view.receivedSamples ?? 0}
                    </dd>
                </dl>
                <p className="notice" data-testid="analysis-state">
                    {view.session?.capture_allowed
                        ? "Analysis permitted by both participants"
                        : "Analysis is off or waiting for both participants' permission and connection."}
                </p>
            </section>
            <section className="panel transcript-panel">
                <p className="eyebrow">LOCAL ASR EVENTS · EXPERIMENTAL</p>
                <h2>Authorized audio transcript</h2>
                <p className="field-hint">
                    Provisional text is replaced as recognition improves. Final
                    rows stay fixed. Energy-based speech boundaries and
                    overlapping windows approximate streaming; cross-participant
                    timing remains receipt-anchored. Showing up to 100 recent
                    rows.
                </p>
                <button
                    className="secondary-button"
                    disabled={!view.session?.capture_allowed}
                    onClick={() => {
                        void controller.current
                            ?.finalize()
                            .catch((e) => setError(liveError(e)));
                    }}
                >
                    Finalize my current speech
                </button>
                <p className="field-hint">
                    Silence normally finalizes speech automatically. Finalize
                    before ending if you need a pending tail; End call and
                    consent revocation discard unfinished audio.
                </p>
                {!transcript.length ? (
                    <p>No authorized transcript event has arrived.</p>
                ) : (
                    <ol>
                        {transcript.map((row) => (
                            <li
                                className={`incremental-row ${row.state}`}
                                key={`${row.sender_user_id}:${row.utterance_id}`}
                                data-utterance={row.utterance_id}
                                data-revision={row.revision}
                                data-state={row.state}
                            >
                                <div className="section-title">
                                    <strong>
                                        {row.sender_user_id.slice(0, 8)}
                                    </strong>
                                    <span
                                        className={`pill ${row.state === "final" ? "positive" : "caution"}`}
                                    >
                                        {row.state === "final"
                                            ? "Final"
                                            : row.state === "failed"
                                              ? "Recognition interrupted"
                                              : "Provisional"}
                                    </span>
                                </div>
                                <p className="field-hint">
                                    {timeLabel(row.start_seconds)}–
                                    {timeLabel(row.end_seconds)} · revision{" "}
                                    {row.revision} ·{" "}
                                    {row.timing === "word"
                                        ? "Model word timing"
                                        : "Estimated word timing"}
                                </p>
                                <p className="revision-text" dir="auto">
                                    {row.text ||
                                        (row.state === "failed"
                                            ? "No usable hypothesis. Recognition is retrying."
                                            : "No words recognized in this speech interval.")}
                                </p>
                                {row.state === "provisional" && (
                                    <small>
                                        {row.agreed_prefix_words} leading words
                                        agree with the preceding hypothesis;
                                        still provisional.
                                    </small>
                                )}
                            </li>
                        ))}
                    </ol>
                )}
            </section>
        </>
    );
}
