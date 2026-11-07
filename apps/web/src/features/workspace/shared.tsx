import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useApiQuery } from "../../lib/api/queries";
import type { WorkspaceContext } from "../../lib/api/generated";
import { ApiError } from "../../lib/api/client";

export function Heading({
    title,
    children,
}: {
    title: string;
    children: ReactNode;
}) {
    return (
        <div className="page-heading">
            <p className="eyebrow">CALL CENTER WORKSPACE</p>
            <h1>{title}</h1>
            <p>{children}</p>
        </div>
    );
}
export function QueryProblem({
    error,
    retry,
}: {
    error: Error;
    retry: () => unknown;
}) {
    const denied = error instanceof ApiError && error.status === 403;
    return (
        <section className="panel problem-panel" role="alert">
            <h2>
                {denied
                    ? "Permission required"
                    : "This view could not be loaded"}
            </h2>
            <p>{error.message}</p>
            <button
                className="secondary-button"
                onClick={() => {
                    void retry();
                }}
            >
                Try again
            </button>
            <Link className="text-button" to="/connect">
                Check workspace access
            </Link>
        </section>
    );
}
export function Pending() {
    return (
        <output className="panel empty-state">
            Loading workspace records…
        </output>
    );
}
export function Empty({
    title,
    children,
}: {
    title: string;
    children: ReactNode;
}) {
    return (
        <section className="panel empty-state">
            <h2>{title}</h2>
            <p>{children}</p>
        </section>
    );
}
export function DataBoundary({ children }: { children: ReactNode }) {
    const context = useApiQuery<WorkspaceContext>(
        "/api/v1/workspace-context",
        "WorkspaceContext",
    );
    if (context.isError)
        return <QueryProblem error={context.error} retry={context.refetch} />;
    if (!context.data) return <Pending />;
    return (
        <>
            <div
                className={`data-notice ${context.data.data_kind === "synthetic_validation" ? "demo-notice" : ""}`}
                role="note"
            >
                <strong>
                    {context.data.data_kind === "synthetic_validation"
                        ? "Synthetic validation records"
                        : "Stored call records"}
                </strong>
                <span>
                    {context.data.data_kind === "synthetic_validation"
                        ? "Demonstration fixtures from the local API. These are not operational results."
                        : "Metrics describe the records available to your account; they do not certify model accuracy."}
                </span>
            </div>
            {children}
        </>
    );
}
export function timeLabel(seconds: number) {
    if (!Number.isFinite(seconds) || seconds < 0) return "Unknown time";
    return `${Math.floor(seconds / 60)}:${(seconds % 60).toFixed(1).padStart(4, "0")}`;
}
export function safeSeek(seconds: number, duration: number): number | null {
    return Number.isFinite(seconds) &&
        Number.isFinite(duration) &&
        duration > 0 &&
        seconds >= 0
        ? Math.min(seconds, duration)
        : null;
}
export function Status({ value }: { value: string }) {
    return (
        <span
            className={`pill ${value === "completed" ? "positive" : value === "failed" ? "caution" : "neutral"}`}
        >
            {value.replaceAll("_", " ")}
        </span>
    );
}
