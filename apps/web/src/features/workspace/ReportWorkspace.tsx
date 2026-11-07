import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import type { CallPage, Report } from "../../lib/api/generated";
import { useApiQuery } from "../../lib/api/queries";
import { Empty, Heading, Pending, QueryProblem, timeLabel } from "./shared";
import { uniqueReferenceTime } from "../calls/CallDetailPage";

type Kind = "qa" | "knowledge" | "coaching" | "emotion" | "receipts";
const titles: Record<Kind, string> = {
    qa: "QA & compliance",
    knowledge: "Knowledge base",
    coaching: "Coaching",
    emotion: "Emotion review",
    receipts: "Report model provenance",
};
export function ReportWorkspace({ kind }: { kind: Kind }) {
    const [selected, setSelected] = useState("");
    const calls = useApiQuery<CallPage>(
        "/api/v1/calls?limit=100&offset=0",
        "CallPage",
    );
    const id = selected || calls.data?.items[0]?.id || "";
    const report = useApiQuery<Report>(
        `/api/v1/calls/${id}/report`,
        "Report",
        Boolean(id) && !calls.isError,
    );
    return (
        <>
            {kind === "receipts" ? (
                <div className="page-heading">
                    <h2>{titles[kind]}</h2>
                    <p>Review the model receipts saved with a selected call.</p>
                </div>
            ) : (
                <Heading title={titles[kind]}>
                    Review stored evidence for a selected call. Predictions
                    remain subject to human verification.
                </Heading>
            )}
            {calls.isError ? (
                <QueryProblem error={calls.error} retry={calls.refetch} />
            ) : !calls.data ? (
                <Pending />
            ) : !calls.data.items.length ? (
                <Empty title="No calls to review">
                    This account has no visible call records.
                </Empty>
            ) : (
                <>
                    <section className="panel call-picker">
                        <label>
                            Select call (latest 100)
                            <select
                                aria-label="Select call"
                                value={id}
                                onChange={(event) =>
                                    setSelected(event.target.value)
                                }
                            >
                                {calls.data.items.map((call) => (
                                    <option value={call.id} key={call.id}>
                                        {call.id.slice(0, 8)} ·{" "}
                                        {new Date(
                                            call.processed_at,
                                        ).toLocaleString()}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <Link className="secondary-button" to={`/calls/${id}`}>
                            Open transcript & playback
                        </Link>
                    </section>
                    {report.isError ? (
                        <QueryProblem
                            error={report.error}
                            retry={report.refetch}
                        />
                    ) : !report.data ? (
                        <Pending />
                    ) : (
                        <ReportContent report={report.data} kind={kind} />
                    )}
                </>
            )}
        </>
    );
}
function Panel({ title, children }: { title: string; children: ReactNode }) {
    return (
        <section className="panel summary-panel">
            <h2>{title}</h2>
            {children}
        </section>
    );
}
function ReportContent({ report, kind }: { report: Report; kind: Kind }) {
    if (kind === "qa") {
        const dimensions = [
            "professionalism",
            "empathy",
            "problem_resolution",
            "compliance",
            "communication_clarity",
        ] as const;
        return (
            <>
                <Panel title="Quality assessment">
                    <p className="large-score">
                        {report.qa_scores.overall_score.toFixed(2)}
                        <span> / 5</span>
                    </p>
                    <p className="muted">
                        Automated assessment, not a verified
                        employee-performance judgment.
                    </p>
                    <div className="dimension-grid">
                        {dimensions.map((key) => (
                            <article className="dimension" key={key}>
                                <h3>{key.replaceAll("_", " ")}</h3>
                                <strong>
                                    {report.qa_scores[key].score} / 5
                                </strong>
                                <p>{report.qa_scores[key].justification}</p>
                            </article>
                        ))}
                    </div>
                </Panel>
                <Panel title="Compliance observations">
                    {report.qa_scores.compliance_flags.length ? (
                        report.qa_scores.compliance_flags.map((flag, index) => {
                            const at = uniqueReferenceTime(
                                flag.transcript_reference,
                                report.transcription.segments,
                            );
                            return (
                                <article key={index} className="evidence-item">
                                    <span className="pill caution">
                                        {flag.severity}
                                    </span>
                                    <h3>{flag.violation}</h3>
                                    <blockquote>
                                        {flag.transcript_reference}
                                    </blockquote>
                                    {at !== null && (
                                        <Link
                                            className="text-button"
                                            to={`/calls/${report.call_id}?at=${at}`}
                                        >
                                            Transcript evidence at{" "}
                                            {timeLabel(at)}
                                        </Link>
                                    )}
                                </article>
                            );
                        })
                    ) : (
                        <p className="muted">
                            No flags were stored. This does not certify
                            compliance.
                        </p>
                    )}
                </Panel>
            </>
        );
    }
    if (kind === "knowledge") {
        const evidence = report.qa_scores.policy_evidence;
        return (
            <Panel title="Policy evidence attached to this report">
                <p className="muted">
                    This view shows saved report citations. Company-wide
                    document search and ingestion are not exposed by the current
                    HTTP API.
                </p>
                {!evidence ||
                evidence.status !== "supported" ||
                !evidence.answer ||
                !evidence.sources?.length ? (
                    <div className="notice">
                        <strong>Evidence unavailable · abstained</strong>
                        <p>
                            {evidence?.reason ||
                                "No supported policy citation was saved for this call."}
                        </p>
                    </div>
                ) : (
                    <>
                        <blockquote className="policy-answer">
                            {evidence.answer}
                        </blockquote>
                        {evidence.sources?.map((source, index) => (
                            <article className="evidence-item" key={index}>
                                <h3>{source.source_id}</h3>
                                <blockquote>{source.passage}</blockquote>
                                <p className="field-hint">
                                    Effective:{" "}
                                    {source.effective_date
                                        ? new Date(
                                              source.effective_date,
                                          ).toLocaleDateString()
                                        : "Not recorded"}{" "}
                                    · Saved report evidence; current policy
                                    access/validity must be rechecked before
                                    reuse.
                                </p>
                            </article>
                        ))}
                    </>
                )}
            </Panel>
        );
    }
    if (kind === "coaching")
        return (
            <>
                <Panel title="Call-specific follow-up">
                    <p className="muted">
                        Stored action items, not a measured improvement in agent
                        performance.
                    </p>
                    {report.summary.action_items.length ? (
                        <ul className="action-list">
                            {report.summary.action_items.map((item, index) => (
                                <li key={index}>
                                    <strong>{item.description}</strong>
                                    <p>
                                        Owner: {item.owner} · Deadline:{" "}
                                        {item.deadline || "Not recorded"}
                                    </p>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p>No action items were stored for this call.</p>
                    )}
                </Panel>
                <Panel title="Communication review">
                    <p>
                        {report.qa_scores.communication_clarity.justification}
                    </p>
                    <Link
                        className="text-button"
                        to={`/calls/${report.call_id}`}
                    >
                        Review the conversation before taking action
                    </Link>
                </Panel>
            </>
        );
    if (kind === "emotion") {
        const emotion = report.acoustic_emotion;
        return (
            <Panel title="Experimental acoustic evidence">
                <div className="notice">
                    <strong>
                        Production emotion analytics remains disabled
                    </strong>
                    <p>
                        Labels are demonstrated only on synthetic validation
                        data in this workspace. They must not determine QA, HR
                        or employee-performance decisions.
                    </p>
                </div>
                {!emotion ? (
                    <p className="muted">
                        No emotion signals are exposed for this report. The
                        existing authorized correction workflow remains
                        separate.
                    </p>
                ) : (
                    <>
                        <p className="muted">{emotion.disclaimer}</p>
                        <p>
                            Status: {emotion.status} · {emotion.model_id} ·{" "}
                            {emotion.model_revision}
                        </p>
                        {emotion.signals?.map((signal, index) => (
                            <article className="evidence-item" key={index}>
                                <span className="pill neutral">
                                    {signal.label}
                                </span>
                                <p>
                                    {signal.reason ||
                                        "Uncalibrated acoustic classifier output"}
                                </p>
                                <p>
                                    Confidence:{" "}
                                    {signal.confidence == null
                                        ? "Unknown"
                                        : `${(signal.confidence * 100).toFixed(1)}% (uncalibrated)`}
                                </p>
                                <Link
                                    className="text-button"
                                    to={`/calls/${report.call_id}?at=${signal.start}`}
                                >
                                    Review audio at {timeLabel(signal.start)}
                                </Link>
                            </article>
                        ))}
                    </>
                )}
                <a className="secondary-button" href="/review-ui/">
                    Open authorized review workflow
                </a>
            </Panel>
        );
    }
    return (
        <Panel title="Inference receipts for the selected report">
            {report.model_runs?.length ? (
                <div className="table-scroll">
                    <table>
                        <caption className="sr-only">
                            Stored inference receipts, not registry promotion
                            records
                        </caption>
                        <thead>
                            <tr>
                                <th>Model</th>
                                <th>Version</th>
                                <th>Provider</th>
                                <th>Prompt</th>
                                <th>Latency</th>
                                <th>Result</th>
                            </tr>
                        </thead>
                        <tbody>
                            {report.model_runs.map((run, index) => (
                                <tr key={index}>
                                    <th scope="row">{run.model_id}</th>
                                    <td>{run.model_version}</td>
                                    <td>{run.provider}</td>
                                    <td>{run.prompt_revision}</td>
                                    <td>{run.latency_ms.toFixed(1)} ms</td>
                                    <td>{run.structured_output}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <p className="muted">
                    No inference receipts were stored. A configured model name
                    is not proof that a model ran.
                </p>
            )}
        </Panel>
    );
}
