import { useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import type { Report } from "../../lib/api/generated";
import { useApiQuery } from "../../lib/api/queries";
import { AudioPlayer } from "./AudioPlayer";
import {
    Heading,
    Pending,
    QueryProblem,
    safeSeek,
    Status,
    timeLabel,
} from "../workspace/shared";

export function uniqueReferenceTime(
    reference: string,
    segments: Report["transcription"]["segments"],
) {
    const quote = reference.trim();
    if (quote.length < 8) return null;
    const matches = segments.filter((segment) => segment.text.includes(quote));
    return matches.length === 1 ? (matches[0]?.start_time ?? null) : null;
}
export function CallDetailPage() {
    const { callId = "" } = useParams();
    const valid =
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
            callId,
        );
    const report = useApiQuery<Report>(
        `/api/v1/calls/${callId}/report`,
        "Report",
        valid,
    );
    const audio = useRef<HTMLAudioElement>(null);
    const [ready, setReady] = useState(false);
    const [params] = useSearchParams();
    const [notice, setNotice] = useState("");
    const at = params.get("at");
    useEffect(() => {
        const target =
            at === null
                ? null
                : safeSeek(Number(at), audio.current?.duration ?? 0);
        if (ready && target !== null && audio.current)
            audio.current.currentTime = target;
    }, [at, ready]);
    function seek(seconds: number) {
        const target = safeSeek(seconds, audio.current?.duration ?? 0);
        if (ready && target !== null && audio.current) {
            audio.current.currentTime = target;
            setNotice(`Playback moved to ${timeLabel(target)}.`);
        }
    }
    if (!valid)
        return (
            <section className="panel empty-state">
                <h1>Invalid call address</h1>
                <Link className="button" to="/calls">
                    Back to calls
                </Link>
            </section>
        );
    if (report.isError)
        return <QueryProblem error={report.error} retry={report.refetch} />;
    if (!report.data) return <Pending />;
    const data = report.data;
    return (
        <>
            <Heading title="Call analysis">
                Recorded analysis, timestamped transcript and the model evidence
                behind it.
            </Heading>
            <div className="call-heading">
                <Link className="text-button" to="/calls">
                    Back to calls
                </Link>
                <Link className="button" to={`/reviews/${callId}`}>
                    Review transcript &amp; QA
                </Link>
                <code>{data.call_id}</code>
                <Status value={data.status} />
            </div>
            <div className="analysis-summary">
                <section className="panel summary-panel">
                    <p className="eyebrow">CALL SUMMARY</p>
                    <h2>{data.summary.call_purpose}</h2>
                    <ul>
                        {data.summary.key_discussion_points.map(
                            (point, index) => (
                                <li key={index}>{point}</li>
                            ),
                        )}
                    </ul>
                    <p className="field-hint">
                        Resolution: {data.summary.resolution_status} · Reported
                        duration:{" "}
                        {data.duration_seconds == null
                            ? "Unknown"
                            : timeLabel(data.duration_seconds)}
                    </p>
                </section>
                <section className="panel score-panel">
                    <p className="eyebrow">QUALITY ASSESSMENT</p>
                    <p className="large-score">
                        {data.qa_scores.overall_score.toFixed(2)}
                        <span> / 5</span>
                    </p>
                    <p>Model-generated score · human review required</p>
                    <p className="field-hint">
                        {data.qa_scores.compliance_flags.length} stored
                        compliance flags. No flags is not proof of compliance.
                    </p>
                </section>
            </div>
            <AudioPlayer
                key={callId}
                audioRef={audio}
                onReady={setReady}
                segments={data.transcription.segments}
            />
            <section className="panel transcript-panel">
                <div className="section-title">
                    <div>
                        <p className="eyebrow">EVIDENCE TRANSCRIPT</p>
                        <h2 id="transcript-heading">Transcript</h2>
                    </div>
                    <span className="pill neutral">
                        {data.transcription.flagged_for_review
                            ? "Review flagged"
                            : "Not human verified"}
                    </span>
                </div>
                <p className="field-hint">
                    Select a local recording to enable timestamp navigation.
                    Speaker labels and timing are model outputs.
                </p>
                <output>{notice}</output>
                <ol className="transcript-list">
                    {data.transcription.segments.map((segment, index) => (
                        <li key={index}>
                            <button
                                className="timestamp"
                                disabled={!ready}
                                onClick={() => seek(segment.start_time)}
                                aria-label={`Seek to ${segment.start_time} seconds`}
                            >
                                {timeLabel(segment.start_time)}
                            </button>
                            <div>
                                <span className="speaker-label">
                                    {segment.speaker_role ||
                                        segment.speaker ||
                                        "Unknown speaker"}
                                </span>
                                {segment.low_confidence && (
                                    <span className="pill caution">
                                        Low confidence
                                    </span>
                                )}
                                <p>{segment.text}</p>
                            </div>
                        </li>
                    ))}
                </ol>
                {!data.transcription.segments.length && (
                    <p className="muted">
                        No timed segments were stored.{" "}
                        {data.transcription.full_text}
                    </p>
                )}
            </section>
            <section className="panel summary-panel">
                <h2>Compliance observations</h2>
                {data.qa_scores.compliance_flags.length ? (
                    data.qa_scores.compliance_flags.map((flag, index) => {
                        const time = uniqueReferenceTime(
                            flag.transcript_reference,
                            data.transcription.segments,
                        );
                        return (
                            <article className="evidence-item" key={index}>
                                <span className="pill caution">
                                    {flag.severity}
                                </span>
                                <h3>{flag.violation}</h3>
                                <blockquote>
                                    {flag.transcript_reference}
                                </blockquote>
                                {time === null ? (
                                    <p className="field-hint">
                                        No unique timed segment matches this
                                        reference.
                                    </p>
                                ) : (
                                    <button
                                        className="text-button"
                                        disabled={!ready}
                                        onClick={() => seek(time)}
                                    >
                                        Listen at {timeLabel(time)}
                                    </button>
                                )}
                            </article>
                        );
                    })
                ) : (
                    <p className="muted">
                        No compliance flags were stored. This does not certify
                        compliance.
                    </p>
                )}
            </section>
        </>
    );
}
