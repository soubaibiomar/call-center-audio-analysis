import { useState } from "react";
import { Link } from "react-router-dom";
import { useApiQuery } from "../../lib/api/queries";
import type { CallPage } from "../../lib/api/generated";
import {
    Empty,
    Heading,
    Pending,
    QueryProblem,
    Status,
} from "../workspace/shared";

export function CallsPage() {
    const [status, setStatus] = useState("");
    const [language, setLanguage] = useState("");
    const [draft, setDraft] = useState("");
    const [offset, setOffset] = useState(0);
    const [sort, setSort] = useState("processed_at");
    const [direction, setDirection] = useState("desc");
    const parameters = new URLSearchParams({
        limit: "20",
        offset: String(offset),
        sort,
        direction,
    });
    if (status) parameters.set("status", status);
    if (language) parameters.set("language", language);
    const calls = useApiQuery<CallPage>(
        `/api/v1/calls?${parameters}`,
        "CallPage",
    );
    function order(column: string) {
        setSort(column);
        setDirection(sort === column && direction === "desc" ? "asc" : "desc");
        setOffset(0);
    }
    return (
        <>
            <Heading title="Calls">
                Find a recording, inspect its analysis and review the evidence.
            </Heading>
            <section className="panel calls-panel">
                <div className="section-title">
                    <div>
                        <p className="eyebrow">RECORDING LIBRARY</p>
                        <h2>Your calls</h2>
                    </div>
                    <button
                        className="secondary-button"
                        onClick={() => {
                            void calls.refetch();
                        }}
                    >
                        {calls.isFetching
                            ? "Refreshing calls…"
                            : "Refresh calls"}
                    </button>
                </div>
                <form
                    className="filter-row"
                    onSubmit={(event) => {
                        event.preventDefault();
                        setLanguage(draft.trim());
                        setOffset(0);
                    }}
                >
                    <label>
                        Status
                        <select
                            aria-label="Status"
                            value={status}
                            onChange={(event) => {
                                setStatus(event.target.value);
                                setOffset(0);
                            }}
                        >
                            <option value="">All statuses</option>
                            <option value="completed">Completed</option>
                            <option value="flagged_for_review">
                                Flagged for review
                            </option>
                            <option value="failed">Failed</option>
                        </select>
                    </label>
                    <label>
                        Language code
                        <input
                            maxLength={30}
                            value={draft}
                            placeholder="e.g. fr, ar, ary"
                            onChange={(event) => setDraft(event.target.value)}
                        />
                    </label>
                    <button className="secondary-button">Apply language</button>
                </form>
                {calls.isError ? (
                    <QueryProblem error={calls.error} retry={calls.refetch} />
                ) : !calls.data ? (
                    <Pending />
                ) : (
                    <>
                        <p className="field-hint">
                            {calls.data.total} matching records · Page{" "}
                            {Math.floor(offset / 20) + 1}. Unknown language is
                            not inferred.
                        </p>
                        <output
                            className="field-hint call-update"
                            data-updated-at={calls.dataUpdatedAt}
                        >
                            Last successful update:{" "}
                            {new Date(calls.dataUpdatedAt).toLocaleTimeString()}
                        </output>
                        {calls.data.items.length === 0 ? (
                            <Empty title="No matching calls">
                                Try another filter. No results is different from
                                an API failure.
                            </Empty>
                        ) : (
                            <div className="table-scroll">
                                <table>
                                    <caption className="sr-only">
                                        Calls available to your account
                                    </caption>
                                    <thead>
                                        <tr>
                                            <th scope="col">Call</th>
                                            <th
                                                scope="col"
                                                aria-sort={
                                                    sort === "processed_at"
                                                        ? direction === "asc"
                                                            ? "ascending"
                                                            : "descending"
                                                        : "none"
                                                }
                                            >
                                                <button
                                                    className="sort-button"
                                                    onClick={() =>
                                                        order("processed_at")
                                                    }
                                                >
                                                    Processed{" "}
                                                    {sort === "processed_at"
                                                        ? direction === "asc"
                                                            ? "↑"
                                                            : "↓"
                                                        : "↕"}
                                                </button>
                                            </th>
                                            <th scope="col">Language</th>
                                            <th
                                                scope="col"
                                                aria-sort={
                                                    sort === "qa_score"
                                                        ? direction === "asc"
                                                            ? "ascending"
                                                            : "descending"
                                                        : "none"
                                                }
                                            >
                                                <button
                                                    className="sort-button"
                                                    onClick={() =>
                                                        order("qa_score")
                                                    }
                                                >
                                                    QA score{" "}
                                                    {sort === "qa_score"
                                                        ? direction === "asc"
                                                            ? "↑"
                                                            : "↓"
                                                        : "↕"}
                                                </button>
                                            </th>
                                            <th scope="col">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {calls.data.items.map((call) => (
                                            <tr key={call.id}>
                                                <th scope="row">
                                                    <Link
                                                        className="record-link"
                                                        to={`/calls/${call.id}`}
                                                    >
                                                        {call.id.slice(0, 8)}…
                                                        <span className="sr-only">
                                                            {" "}
                                                            Open call {call.id}
                                                        </span>
                                                    </Link>
                                                </th>
                                                <td>
                                                    {new Date(
                                                        call.processed_at,
                                                    ).toLocaleString()}
                                                </td>
                                                <td>
                                                    {call.language || "Unknown"}
                                                </td>
                                                <td>
                                                    {call.qa_score === null
                                                        ? "Not scored"
                                                        : `${call.qa_score.toFixed(2)} / 5`}
                                                </td>
                                                <td>
                                                    <Status
                                                        value={call.status}
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                        <div className="pagination">
                            <button
                                className="secondary-button"
                                disabled={offset === 0}
                                onClick={() =>
                                    setOffset(Math.max(0, offset - 20))
                                }
                            >
                                Previous page
                            </button>
                            <button
                                className="secondary-button"
                                disabled={
                                    offset + 20 >= calls.data.total ||
                                    offset >= 10000
                                }
                                onClick={() => setOffset(offset + 20)}
                            >
                                Next page
                            </button>
                        </div>
                    </>
                )}
            </section>
        </>
    );
}
