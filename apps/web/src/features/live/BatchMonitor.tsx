import { useState, type FormEvent } from "react";
import type { JobStatus } from "../../lib/api/generated";
import { useApiQuery } from "../../lib/api/queries";
import { Pending, QueryProblem, Status } from "../workspace/shared";

export function BatchMonitor() {
    const [draft, setDraft] = useState("");
    const [id, setId] = useState("");
    const [poll, setPoll] = useState(false);
    const [error, setError] = useState("");
    const job = useApiQuery<JobStatus>(
        `/api/v1/jobs/${id}`,
        "JobStatus",
        Boolean(id),
        poll ? 3000 : undefined,
    );
    function submit(event: FormEvent) {
        event.preventDefault();
        if (
            !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
                draft.trim(),
            )
        ) {
            setError("Enter a valid job UUID.");
            return;
        }
        setError("");
        setId(draft.trim());
        setPoll(true);
    }
    return (
        <>
            <section className="panel summary-panel">
                <div className="section-title">
                    <div>
                        <p className="eyebrow">
                            BATCH PROCESSING · NOT A LIVE CALL
                        </p>
                        <h2>Monitor an existing job</h2>
                    </div>
                    {id && (
                        <button
                            className="secondary-button"
                            onClick={() => setPoll(!poll)}
                        >
                            {poll ? "Pause updates" : "Resume updates"}
                        </button>
                    )}
                </div>
                <form className="filter-row" onSubmit={submit}>
                    <label>
                        Job identifier
                        <input
                            maxLength={36}
                            value={draft}
                            onChange={(event) => setDraft(event.target.value)}
                            placeholder="Job UUID"
                            required
                        />
                    </label>
                    <button className="button">Monitor job</button>
                </form>
                {error && (
                    <p role="alert" className="error-message">
                        {error}
                    </p>
                )}
                {!id ? (
                    <p className="muted">
                        Enter an existing job ID. No job or call is created by
                        this screen.
                    </p>
                ) : job.isError ? (
                    <QueryProblem error={job.error} retry={job.refetch} />
                ) : !job.data ? (
                    <Pending />
                ) : (
                    <div className="job-state">
                        <Status value={job.data.status} />
                        <dl>
                            <dt>Attempts</dt>
                            <dd>{job.data.attempts}</dd>
                            <dt>Queue</dt>
                            <dd>{job.data.queue || "Not recorded"}</dd>
                            <dt>Progress</dt>
                            <dd>
                                {job.data.progress == null
                                    ? "Percentage not measured"
                                    : `${(job.data.progress * 100).toFixed(1)}%`}
                            </dd>
                            <dt>Error code</dt>
                            <dd>{job.data.error_code || "None recorded"}</dd>
                        </dl>
                        <p className="field-hint">
                            {poll
                                ? "Refreshing every 3 seconds"
                                : "Automatic updates paused"}
                            . Phase transitions are API records, not proof of
                            live audio processing.
                        </p>
                    </div>
                )}
            </section>
        </>
    );
}
