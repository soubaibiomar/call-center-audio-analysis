import { Link } from "react-router-dom";
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    PieChart,
    Pie,
    Cell,
} from "recharts";
import type { Activity, CallPage, Dashboard } from "../../lib/api/generated";
import { useApiQuery } from "../../lib/api/queries";
import {
    Heading,
    Pending,
    QueryProblem,
    Status,
    Empty,
} from "../workspace/shared";

const palette = ["#1D5B49", "#53865B", "#9BC77B", "#CBD8C5", "#737E71"];
export function DashboardPage() {
    const metrics = useApiQuery<Dashboard>("/api/v1/dashboard", "Dashboard");
    const activity = useApiQuery<Activity>(
        "/api/v1/dashboard/activity?days=30",
        "Activity",
    );
    const recent = useApiQuery<CallPage>(
        "/api/v1/calls?limit=5&offset=0",
        "CallPage",
    );
    if (metrics.isError)
        return <QueryProblem error={metrics.error} retry={metrics.refetch} />;
    if (!metrics.data) return <Pending />;
    const data = metrics.data;
    return (
        <>
            <Heading title="Overview">
                A measured view of your call operations, with evidence close at
                hand.
            </Heading>
            <p className="scope-label">
                Scope:{" "}
                {data.scope === "tenant" ? "your tenant" : "your owned calls"} ·
                Totals cover stored records; charts cover the last 30 UTC dates.
            </p>
            <div className="metric-grid">
                {[
                    ["Total calls", data.total_calls],
                    ["Completed", data.completed],
                    ["Needs review", data.flagged_for_review],
                    ["Failed", data.failed],
                    [
                        "Average QA",
                        data.average_qa_score === null
                            ? "Not scored"
                            : `${data.average_qa_score.toFixed(2)} / 5`,
                    ],
                ].map(([name, value]) => (
                    <section className="panel metric-card" key={String(name)}>
                        <h2>{name}</h2>
                        <p>{value}</p>
                        <span>Stored API records</span>
                    </section>
                ))}
            </div>
            {activity.isError ? (
                <QueryProblem error={activity.error} retry={activity.refetch} />
            ) : !activity.data ? (
                <Pending />
            ) : (
                <div className="analytics-grid">
                    <section className="panel chart-panel">
                        <p className="eyebrow">LAST 30 DAYS · UTC</p>
                        <h2>Call volume</h2>
                        <figure
                            className="chart-frame"
                            aria-label="Daily stored call counts; exact values are available in the table below"
                        >
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart
                                    data={activity.data.days}
                                    accessibilityLayer
                                >
                                    <CartesianGrid
                                        vertical={false}
                                        stroke="#E4E8E1"
                                    />
                                    <XAxis
                                        dataKey="date"
                                        tickFormatter={(date) =>
                                            String(date).slice(5)
                                        }
                                        stroke="#56645D"
                                        tick={{ fontSize: 11 }}
                                        minTickGap={30}
                                    />
                                    <YAxis
                                        allowDecimals={false}
                                        width={30}
                                        stroke="#56645D"
                                        tick={{ fontSize: 11 }}
                                    />
                                    <Line
                                        dataKey="calls"
                                        stroke="#1D5B49"
                                        strokeWidth={3}
                                        dot={false}
                                        isAnimationActive={false}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </figure>
                        <details>
                            <summary>View daily counts</summary>
                            <table>
                                <caption className="sr-only">
                                    Exact daily count data
                                </caption>
                                <thead>
                                    <tr>
                                        <th>Date, UTC</th>
                                        <th>Calls</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {activity.data.days.map((day) => (
                                        <tr key={day.date}>
                                            <th scope="row">{day.date}</th>
                                            <td>{day.calls}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </details>
                    </section>
                    <section className="panel chart-panel">
                        <p className="eyebrow">RECORDED METADATA</p>
                        <h2>Languages</h2>
                        {activity.data.languages.length ? (
                            <>
                                <figure
                                    className="chart-frame"
                                    aria-label="Recorded language distribution; exact counts follow"
                                >
                                    <ResponsiveContainer
                                        width="100%"
                                        height="100%"
                                    >
                                        <PieChart>
                                            <Pie
                                                data={activity.data.languages}
                                                dataKey="calls"
                                                nameKey="language"
                                                innerRadius="60%"
                                                outerRadius="85%"
                                                isAnimationActive={false}
                                            >
                                                {activity.data.languages.map(
                                                    (language, index) => (
                                                        <Cell
                                                            key={
                                                                language.language
                                                            }
                                                            fill={
                                                                palette[
                                                                    index %
                                                                        palette.length
                                                                ]
                                                            }
                                                        />
                                                    ),
                                                )}
                                            </Pie>
                                        </PieChart>
                                    </ResponsiveContainer>
                                </figure>
                                <ul className="language-list">
                                    {activity.data.languages.map(
                                        (item, index) => (
                                            <li key={item.language}>
                                                <span
                                                    className="legend-dot"
                                                    style={{
                                                        background:
                                                            palette[
                                                                index %
                                                                    palette.length
                                                            ],
                                                    }}
                                                    aria-hidden="true"
                                                />
                                                {item.language}
                                                <strong>{item.calls}</strong>
                                            </li>
                                        ),
                                    )}
                                </ul>
                            </>
                        ) : (
                            <p className="muted">
                                No language records in this window. No
                                distribution is estimated.
                            </p>
                        )}
                    </section>
                </div>
            )}
            <section className="panel calls-panel">
                <div className="section-title">
                    <h2>Recent calls</h2>
                    <Link className="secondary-button" to="/calls">
                        View all calls
                    </Link>
                </div>
                {recent.isError ? (
                    <QueryProblem error={recent.error} retry={recent.refetch} />
                ) : !recent.data ? (
                    <Pending />
                ) : recent.data.items.length ? (
                    <div className="table-scroll">
                        <table>
                            <caption className="sr-only">
                                Five most recent visible calls
                            </caption>
                            <thead>
                                <tr>
                                    <th>Call</th>
                                    <th>Processed</th>
                                    <th>Language</th>
                                    <th>QA</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recent.data.items.map((call) => (
                                    <tr key={call.id}>
                                        <th scope="row">
                                            <Link
                                                className="record-link"
                                                to={`/calls/${call.id}`}
                                            >
                                                {call.id.slice(0, 8)}…
                                            </Link>
                                        </th>
                                        <td>
                                            {new Date(
                                                call.processed_at,
                                            ).toLocaleString()}
                                        </td>
                                        <td>{call.language || "Unknown"}</td>
                                        <td>
                                            {call.qa_score === null
                                                ? "Not scored"
                                                : `${call.qa_score.toFixed(2)} / 5`}
                                        </td>
                                        <td>
                                            <Status value={call.status} />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <Empty title="No calls yet">
                        No call records are available to this account.
                    </Empty>
                )}
            </section>
        </>
    );
}
