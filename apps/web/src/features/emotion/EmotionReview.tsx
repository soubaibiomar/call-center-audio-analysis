import { useEffect, useRef, useState, type FormEvent } from "react";

type Vote = {
    reviewer_id: string;
    label: string;
    notes: string;
    version: number;
};
type Item = {
    id: string;
    call_id: string;
    source_audio_sha256: string;
    partition: string;
    revision: number;
    consent_to_train: boolean;
    prediction: {
        label: string;
        start: number;
        end: number;
        model_id: string;
        model_revision: string;
        confidence: number | null;
        probabilities: Record<string, number>;
    };
    status: string;
    corrected_label: string | null;
    votes: Vote[];
    adjudication_note: string | null;
    eligible_for_training: boolean;
};
type Identity = { user_id: string; role: string };
const labels = [
    ["neutral", "Neutral"],
    ["happy", "Happy"],
    ["angry", "Angry"],
    ["sad", "Sad"],
    ["Unknown", "Uncertain / abstain"],
];

export function EmotionReview() {
    const [token, setToken] = useState(""),
        [credential, setCredential] = useState(""),
        [identity, setIdentity] = useState<Identity | null>(null);
    const [items, setItems] = useState<Item[]>([]),
        [selected, setSelected] = useState(""),
        [filter, setFilter] = useState("");
    const [label, setLabel] = useState("Unknown"),
        [notes, setNotes] = useState(""),
        [confirmed, setConfirmed] = useState(false);
    const [error, setError] = useState(""),
        [notice, setNotice] = useState(""),
        [busy, setBusy] = useState(false),
        [audio, setAudio] = useState("");
    const [consent, setConsent] = useState(false),
        [evidence, setEvidence] = useState("");
    const player = useRef<HTMLAudioElement>(null);
    const item = items.find((i) => i.id === selected);
    const ownVote = item?.votes.find(
        (v) => v.reviewer_id === identity?.user_id,
    );
    async function request(
        path: string,
        method = "GET",
        body?: unknown,
        access = token,
    ) {
        const response = await fetch("/api/v1" + path, {
            method,
            headers: {
                Authorization: "Bearer " + access,
                ...(body ? { "Content-Type": "application/json" } : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
            cache: "no-store",
        });
        if (!response.ok)
            throw new Error(
                response.status === 409
                    ? "This item changed. Refresh and review the current version."
                    : response.status === 401 || response.status === 503
                      ? "Reviewer access is unavailable or expired. Connect with an enabled reviewer identity."
                      : response.status === 403
                        ? "This action needs a different reviewer permission."
                        : response.status === 422
                          ? "Check the required confirmation and fields."
                          : "The review could not be loaded or saved.",
            );
        return response.status === 204 ? null : response.json();
    }
    async function load(access = token) {
        const result: Item[] = await request(
            "/emotion-reviews",
            "GET",
            undefined,
            access,
        );
        setItems(result);
        setSelected((previous) =>
            result.some((i) => i.id === previous)
                ? previous
                : (result[0]?.id ?? ""),
        );
    }
    async function connect(event: FormEvent) {
        event.preventDefault();
        setBusy(true);
        setError("");
        try {
            const who = await request("/me", "GET", undefined, credential);
            if (!["supervisor", "admin"].includes(who.role))
                throw new Error(
                    "An enabled supervisor or administrator account is required.",
                );
            await load(credential);
            setIdentity(who);
            setToken(credential);
            setCredential("");
        } catch (e) {
            setError((e as Error).message);
        } finally {
            setBusy(false);
        }
    }
    function disconnect() {
        setToken("");
        setCredential("");
        setIdentity(null);
        setItems([]);
        setSelected("");
        setNotice("");
        setError("");
    }
    useEffect(() => {
        setLabel("Unknown");
        setNotes("");
        setConfirmed(false);
        setConsent(item?.consent_to_train ?? false);
        setEvidence("");
        setAudio("");
        setNotice("");
    }, [selected]);
    useEffect(
        () => () => {
            if (audio) URL.revokeObjectURL(audio);
        },
        [audio],
    );
    async function chooseAudio(file?: File) {
        setAudio("");
        setConfirmed(false);
        setError("");
        if (!file || !item) return;
        try {
            if (file.size > 50 * 1024 * 1024)
                throw new Error("Choose a recording smaller than 50 MB.");
            const digest = Array.from(
                new Uint8Array(
                    await crypto.subtle.digest(
                        "SHA-256",
                        await file.arrayBuffer(),
                    ),
                ),
            )
                .map((n) => n.toString(16).padStart(2, "0"))
                .join("");
            if (digest !== item.source_audio_sha256)
                throw new Error(
                    "This recording does not match the enrolled source checksum.",
                );
            setAudio(URL.createObjectURL(file));
        } catch (e) {
            setError((e as Error).message);
        }
    }
    async function mutate(
        path: string,
        method: string,
        body?: unknown,
        message = "Review saved.",
    ) {
        setBusy(true);
        setError("");
        try {
            const result = await request(path, method, body);
            await load();
            setConfirmed(false);
            setNotice(
                path.endsWith("/votes") && result?.status === "verified"
                    ? "Your review is saved. Correction verified by independent reviewers; training permission remains separate."
                    : message,
            );
        } catch (e) {
            setError((e as Error).message);
        } finally {
            setBusy(false);
        }
    }
    async function submit(event: FormEvent) {
        event.preventDefault();
        if (!item || !audio || !confirmed) return;
        await mutate(
            `/emotion-reviews/${item.id}/votes`,
            "POST",
            { label, notes, confirmed: true, expected_revision: item.revision },
            "Your review is saved. A second independent review is required for verification.",
        );
    }
    const visible = items.filter((i) =>
        i.call_id.toLowerCase().includes(filter.toLowerCase()),
    );
    return (
        <div className="app">
            <a className="skip" href="#review">
                Skip to review
            </a>
            <header>
                <div className="brand">
                    Adaptive <span>Call Center Intelligence</span>
                </div>
                <div className="header-right">
                    <span className="subtle">Human review workspace</span>
                    {identity && (
                        <button className="quiet" onClick={disconnect}>
                            Sign out
                        </button>
                    )}
                </div>
            </header>
            <div className="layout">
                <aside>
                    <p className="eyebrow">WORKSPACE</p>
                    <nav aria-label="Review navigation">
                        <a className="active" href="#review">
                            Emotion review
                        </a>
                        <a href="#safeguards">Review safeguards</a>
                    </nav>
                    <div className="aside-note">
                        <p className="eyebrow">RESEARCH STATUS</p>
                        <strong>Human judgement matters.</strong>
                        <p>
                            Acoustic labels are uncertain observations. They do
                            not measure true feelings.
                        </p>
                    </div>
                </aside>
                <main id="review">
                    <div className="page-heading">
                        <div>
                            <p className="eyebrow">QUALITY & LEARNING</p>
                            <h1>
                                Review the signal.
                                <br className="mobile-only" /> Keep the context.
                            </h1>
                            <p className="subtle">
                                Confirm a segment, preserve the original, and
                                make uncertainty explicit.
                            </p>
                        </div>
                        <span className="pill">Emotion annotations</span>
                    </div>
                    <section className="safeguard" id="safeguards">
                        <strong>Research use · no automatic scoring</strong>
                        <p>
                            Corrections never overwrite model predictions or
                            change employee scores. Training needs separate
                            permission and independent review. Evaluation
                            records stay protected.
                        </p>
                    </section>
                    {error && (
                        <div role="alert" className="error">
                            {error}
                        </div>
                    )}
                    {notice && (
                        <div role="status" className="success">
                            {notice}
                        </div>
                    )}
                    {!identity ? (
                        <section className="card access">
                            <p className="eyebrow">REVIEWER ACCESS</p>
                            <h2>Connect your reviewer account</h2>
                            <p>
                                Use an access token from the configured identity
                                provider. It stays in this page’s memory and is
                                cleared on sign out.
                            </p>
                            <form onSubmit={connect}>
                                <label htmlFor="access">
                                    Reviewer access token
                                </label>
                                <input
                                    id="access"
                                    type="password"
                                    autoComplete="off"
                                    value={credential}
                                    onChange={(e) =>
                                        setCredential(e.target.value)
                                    }
                                    required
                                />
                                <button disabled={busy}>
                                    {busy
                                        ? "Connecting…"
                                        : "Connect to review queue"}
                                </button>
                            </form>
                        </section>
                    ) : (
                        <>
                            <div className="queue-toolbar">
                                <div>
                                    <strong>{items.length} items shown</strong>
                                    <span className="subtle">
                                        {" "}
                                        · {identity.role} access
                                    </span>
                                </div>
                                <button
                                    className="quiet"
                                    disabled={busy}
                                    onClick={() => {
                                        setBusy(true);
                                        setError("");
                                        load()
                                            .catch((e) => setError(e.message))
                                            .finally(() => setBusy(false));
                                    }}
                                >
                                    Refresh queue
                                </button>
                            </div>
                            <div className="review-grid">
                                <section className="card queue">
                                    <h2>Review queue</h2>
                                    <label htmlFor="filter">
                                        Find by call reference
                                    </label>
                                    <input
                                        id="filter"
                                        type="search"
                                        placeholder="Search call reference"
                                        value={filter}
                                        onChange={(e) =>
                                            setFilter(e.target.value)
                                        }
                                    />
                                    <div className="queue-items">
                                        {visible.map((i) => (
                                            <button
                                                key={i.id}
                                                className={
                                                    "queue-item " +
                                                    (i.id === selected
                                                        ? "selected"
                                                        : "")
                                                }
                                                onClick={() =>
                                                    setSelected(i.id)
                                                }
                                            >
                                                <span>
                                                    Call {i.call_id.slice(0, 8)}
                                                </span>
                                                <small>
                                                    {i.prediction.start.toFixed(
                                                        1,
                                                    )}
                                                    –
                                                    {i.prediction.end.toFixed(
                                                        1,
                                                    )}
                                                    s · {i.status}
                                                </small>
                                                <small>
                                                    {i.partition ===
                                                    "evaluation"
                                                        ? "Protected evaluation"
                                                        : "Review collection"}
                                                </small>
                                            </button>
                                        ))}
                                        {!visible.length && (
                                            <p className="empty">
                                                No matching items. An
                                                administrator must enroll an
                                                eligible segment before review.
                                            </p>
                                        )}
                                    </div>
                                </section>
                                {item ? (
                                    <div className="detail">
                                        <section className="card">
                                            <div className="section-heading">
                                                <h2>Source segment</h2>
                                                <span className="pill">
                                                    {item.prediction.start.toFixed(
                                                        1,
                                                    )}
                                                    –
                                                    {item.prediction.end.toFixed(
                                                        1,
                                                    )}{" "}
                                                    seconds
                                                </span>
                                            </div>
                                            <p className="subtle">
                                                Choose the enrolled recording
                                                from your laptop. It stays
                                                local; the checksum must match.
                                            </p>
                                            <label htmlFor="audio-file">
                                                Local source recording
                                            </label>
                                            <input
                                                id="audio-file"
                                                type="file"
                                                accept="audio/*"
                                                onChange={(e) =>
                                                    chooseAudio(
                                                        e.target.files?.[0],
                                                    )
                                                }
                                            />
                                            {audio && (
                                                <div className="playback">
                                                    <audio
                                                        ref={player}
                                                        controls
                                                        src={audio}
                                                    />
                                                    <button
                                                        className="quiet"
                                                        onClick={() => {
                                                            if (
                                                                player.current
                                                            ) {
                                                                player.current.currentTime =
                                                                    item.prediction.start;
                                                                void player.current.play();
                                                            }
                                                        }}
                                                    >
                                                        Play segment start
                                                    </button>
                                                </div>
                                            )}
                                        </section>
                                        <div className="comparison">
                                            <section className="card original">
                                                <p className="eyebrow">
                                                    ORIGINAL MODEL OUTPUT
                                                </p>
                                                <h2>{item.prediction.label}</h2>
                                                <p className="subtle">
                                                    Uncalibrated · retained
                                                    unchanged
                                                </p>
                                                <dl>
                                                    {Object.entries(
                                                        item.prediction
                                                            .probabilities,
                                                    ).map(([name, value]) => (
                                                        <div key={name}>
                                                            <dt>{name}</dt>
                                                            <dd>
                                                                {(
                                                                    value * 100
                                                                ).toFixed(1)}
                                                                %
                                                            </dd>
                                                        </div>
                                                    ))}
                                                </dl>
                                                <p className="model-ref">
                                                    {item.prediction.model_id}
                                                    <br />
                                                    Revision{" "}
                                                    {item.prediction.model_revision.slice(
                                                        0,
                                                        12,
                                                    )}
                                                </p>
                                            </section>
                                            <section className="card corrected">
                                                <p className="eyebrow">
                                                    REVIEWED CORRECTION
                                                </p>
                                                <h2>
                                                    {item.corrected_label ??
                                                        "Awaiting verification"}
                                                </h2>
                                                <p className="subtle">
                                                    {item.status} ·{" "}
                                                    {item.votes.length} reviewer
                                                    {item.votes.length === 1
                                                        ? ""
                                                        : "s"}
                                                </p>
                                                <p>
                                                    {item.eligible_for_training
                                                        ? "Eligible for the live training manifest; training is a separate action."
                                                        : "Excluded from the training manifest until all safeguards pass."}
                                                </p>
                                                {item.votes.map((v) => (
                                                    <p
                                                        key={v.reviewer_id}
                                                        className="vote-line"
                                                    >
                                                        Reviewer{" "}
                                                        {v.reviewer_id.slice(
                                                            0,
                                                            8,
                                                        )}{" "}
                                                        · {v.label}
                                                        <br />
                                                        <small>
                                                            {v.notes ||
                                                                "No notes"}
                                                        </small>
                                                    </p>
                                                ))}
                                                {item.adjudication_note && (
                                                    <p>
                                                        Adjudication:{" "}
                                                        {item.adjudication_note}
                                                    </p>
                                                )}
                                            </section>
                                        </div>
                                        <section className="card">
                                            <h2>Your review</h2>
                                            <p className="subtle">
                                                Describe the acoustic
                                                expression, not the person’s
                                                mental state. Choose uncertainty
                                                whenever context is
                                                insufficient.
                                            </p>
                                            <form onSubmit={submit}>
                                                <fieldset>
                                                    <legend>
                                                        Corrected label
                                                    </legend>
                                                    <div className="label-options">
                                                        {labels.map(
                                                            ([value, text]) => (
                                                                <label
                                                                    key={value}
                                                                    className={
                                                                        label ===
                                                                        value
                                                                            ? "chosen"
                                                                            : ""
                                                                    }
                                                                >
                                                                    <input
                                                                        type="radio"
                                                                        name="label"
                                                                        value={
                                                                            value
                                                                        }
                                                                        checked={
                                                                            label ===
                                                                            value
                                                                        }
                                                                        onChange={() =>
                                                                            setLabel(
                                                                                value,
                                                                            )
                                                                        }
                                                                    />
                                                                    {text}
                                                                </label>
                                                            ),
                                                        )}
                                                    </div>
                                                </fieldset>
                                                <label htmlFor="notes">
                                                    Reviewer notes{" "}
                                                    <span className="subtle">
                                                        (optional; no personal
                                                        data)
                                                    </span>
                                                </label>
                                                <textarea
                                                    id="notes"
                                                    maxLength={2000}
                                                    value={notes}
                                                    onChange={(e) =>
                                                        setNotes(e.target.value)
                                                    }
                                                    placeholder="Describe audible cues or why the segment is uncertain."
                                                />
                                                <label className="check">
                                                    <input
                                                        type="checkbox"
                                                        checked={confirmed}
                                                        disabled={!audio}
                                                        onChange={(e) =>
                                                            setConfirmed(
                                                                e.target
                                                                    .checked,
                                                            )
                                                        }
                                                    />
                                                    I reviewed the matching
                                                    source segment and confirm
                                                    this uncertain acoustic
                                                    judgement.
                                                </label>
                                                <div className="actions">
                                                    <button
                                                        disabled={
                                                            busy ||
                                                            !confirmed ||
                                                            !audio
                                                        }
                                                    >
                                                        {busy
                                                            ? "Saving…"
                                                            : ownVote
                                                              ? "Update my review"
                                                              : "Save my review"}
                                                    </button>
                                                    {ownVote && (
                                                        <button
                                                            type="button"
                                                            className="quiet"
                                                            disabled={busy}
                                                            onClick={() =>
                                                                mutate(
                                                                    `/emotion-reviews/${item.id}/votes/me`,
                                                                    "DELETE",
                                                                    undefined,
                                                                    "Your correction was revoked and training eligibility refreshed.",
                                                                )
                                                            }
                                                        >
                                                            Revoke my correction
                                                        </button>
                                                    )}
                                                </div>
                                                {identity.role === "admin" &&
                                                    item.status ===
                                                        "disagreement" && (
                                                        <button
                                                            type="button"
                                                            className="quiet"
                                                            disabled={
                                                                busy ||
                                                                !confirmed ||
                                                                !audio ||
                                                                notes.length <
                                                                    10 ||
                                                                !!ownVote
                                                            }
                                                            onClick={() =>
                                                                mutate(
                                                                    `/emotion-reviews/${item.id}/adjudicate`,
                                                                    "POST",
                                                                    {
                                                                        label,
                                                                        notes,
                                                                        confirmed: true,
                                                                        expected_revision:
                                                                            item.revision,
                                                                    },
                                                                    "Independent adjudication saved.",
                                                                )
                                                            }
                                                        >
                                                            Reconcile
                                                            disagreement
                                                            (independent admin)
                                                        </button>
                                                    )}
                                            </form>
                                        </section>
                                        {identity.role === "admin" && (
                                            <section className="card permission">
                                                <h2>Training permission</h2>
                                                <p>
                                                    Annotation alone is not
                                                    consent. An administrator
                                                    must attest a valid,
                                                    purpose-specific permission
                                                    reference.
                                                </p>
                                                <label className="check">
                                                    <input
                                                        type="checkbox"
                                                        checked={consent}
                                                        disabled={
                                                            item.partition ===
                                                            "evaluation"
                                                        }
                                                        onChange={(e) =>
                                                            setConsent(
                                                                e.target
                                                                    .checked,
                                                            )
                                                        }
                                                    />
                                                    Permission covers training
                                                </label>
                                                <label htmlFor="evidence">
                                                    Permission evidence
                                                    reference
                                                </label>
                                                <input
                                                    id="evidence"
                                                    maxLength={300}
                                                    value={evidence}
                                                    onChange={(e) =>
                                                        setEvidence(
                                                            e.target.value,
                                                        )
                                                    }
                                                />
                                                <div className="actions">
                                                    <button
                                                        disabled={
                                                            busy ||
                                                            !evidence.trim()
                                                        }
                                                        onClick={() =>
                                                            mutate(
                                                                `/emotion-reviews/${item.id}/consent`,
                                                                "PATCH",
                                                                {
                                                                    consent_to_train:
                                                                        consent,
                                                                    consent_evidence:
                                                                        evidence,
                                                                    expected_revision:
                                                                        item.revision,
                                                                },
                                                                "Training permission updated; live membership refreshed.",
                                                            )
                                                        }
                                                    >
                                                        Save permission
                                                    </button>
                                                    <button
                                                        className="danger"
                                                        disabled={busy}
                                                        onClick={() => {
                                                            if (
                                                                window.confirm(
                                                                    "Delete this annotation and all reviewer corrections? The original inference remains in its call report.",
                                                                )
                                                            )
                                                                void mutate(
                                                                    `/emotion-reviews/${item.id}`,
                                                                    "DELETE",
                                                                    undefined,
                                                                    "Annotation deleted; removed from the live training manifest.",
                                                                );
                                                        }}
                                                    >
                                                        Delete annotation
                                                    </button>
                                                </div>
                                            </section>
                                        )}
                                    </div>
                                ) : (
                                    <section className="card empty">
                                        <h2>Nothing to review yet</h2>
                                        <p>
                                            Choose an accessible item from the
                                            queue, or ask an administrator to
                                            enroll a source segment.
                                        </p>
                                    </section>
                                )}
                            </div>
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
