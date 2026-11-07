import { expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { App } from "../../app/App";
import { AuthProvider } from "../../app/auth";
import { safeSeek } from "./shared";
import { uniqueReferenceTime } from "../calls/CallDetailPage";
import { buildWebVtt } from "../calls/AudioPlayer";
import { validateResource } from "../../lib/api/queries";
import type { TranscriptionSegment } from "../../lib/api/generated";

const identity = {
    tenant_id: "00000000-0000-4000-8000-000000000001",
    user_id: "00000000-0000-4000-8000-000000000002",
    role: "admin",
};
const context = {
    data_kind: "synthetic_validation",
    live_transport: "not_available",
    training_controls: "not_available",
};
const empty = { items: [], total: 0, limit: 20, offset: 0 };
const segment: TranscriptionSegment = {
    text: "Unique evidence quote.",
    start_time: 1.25,
    end_time: 2.5,
    speaker: "Unknown",
    confidence: 0.5,
    low_confidence: true,
};
async function mount(
    path: string,
    response: (path: string) => Response | Promise<Response>,
) {
    vi.stubGlobal(
        "fetch",
        vi.fn((url: string) =>
            Promise.resolve(
                url === "/api/v1/me"
                    ? new Response(JSON.stringify(identity))
                    : url === "/api/v1/workspace-context"
                      ? new Response(JSON.stringify(context))
                      : response(url),
            ),
        ),
    );
    const client = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    render(
        <QueryClientProvider client={client}>
            <AuthProvider>
                <MemoryRouter initialEntries={[path]}>
                    <App />
                </MemoryRouter>
            </AuthProvider>
        </QueryClientProvider>,
    );
    const user = userEvent.setup();
    await user.type(
        await screen.findByLabelText("Workspace access token"),
        "synthetic-token",
    );
    await user.click(screen.getByRole("button", { name: "Connect securely" }));
    return user;
}
it("shows a real empty state only after a successful empty call response", async () => {
    await mount("/calls", () => new Response(JSON.stringify(empty)));
    expect(
        await screen.findByRole("heading", { name: "No matching calls" }),
    ).toBeVisible();
    expect(screen.getByText("Synthetic validation records")).toBeVisible();
});
it("does not show fake empty success on an API failure; retry loads the response", async () => {
    let failed = true;
    const user = await mount("/calls", () =>
        failed
            ? new Response("private-error", { status: 503 })
            : new Response(JSON.stringify(empty)),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("not ready");
    expect(
        screen.queryByRole("heading", { name: "No matching calls" }),
    ).not.toBeInTheDocument();
    failed = false;
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(
        await screen.findByRole("heading", { name: "No matching calls" }),
    ).toBeVisible();
});
it("rejects malformed call contracts instead of rendering invented totals", async () => {
    await mount(
        "/calls",
        () =>
            new Response(
                '{"items":[],"total":"invented","limit":20,"offset":0}',
            ),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
        "unexpected response",
    );
    expect(screen.queryByText(/matching records/)).not.toBeInTheDocument();
});
it("renders registry permission denied separately from an empty registry", async () => {
    await mount("/models", (path) =>
        path.startsWith("/api/v1/model-versions")
            ? new Response("", { status: 403 })
            : new Response(JSON.stringify(empty)),
    );
    expect(
        await screen.findByRole("heading", { name: "Permission required" }),
    ).toBeVisible();
    expect(
        screen.queryByRole("heading", { name: "No registered model versions" }),
    ).not.toBeInTheDocument();
});
it("bounds seeking and rejects unavailable or invalid timing", () => {
    expect(safeSeek(1.25, 4)).toBe(1.25);
    expect(safeSeek(50, 4)).toBe(4);
    for (const value of [-1, NaN, Infinity])
        expect(safeSeek(value, 4)).toBeNull();
    expect(safeSeek(1, 0)).toBeNull();
});
it("links compliance quotes only to a unique timed segment", () => {
    expect(uniqueReferenceTime(segment.text, [segment])).toBe(1.25);
    expect(uniqueReferenceTime(segment.text, [segment, segment])).toBeNull();
    expect(uniqueReferenceTime("yes", [segment])).toBeNull();
});
it("creates escaped timed captions and drops invalid segments", () => {
    const text = buildWebVtt([
        { ...segment, text: "<script> & caption" },
        { ...segment, start_time: -1 },
    ]);
    expect(text).toContain("00:00:01.250 --> 00:00:02.500");
    expect(text).toContain("&lt;script&gt; &amp; caption");
    expect(text).not.toContain("<script>");
    expect(text.match(/-->/g)).toHaveLength(1);
    expect(
        buildWebVtt([{ ...segment, start_time: 59.9999, end_time: 60.5 }]),
    ).toContain("00:01:00.000 --> 00:01:00.500");
    expect(
        buildWebVtt([{ ...segment, start_time: 1, end_time: 1.0001 }]),
    ).not.toContain("-->");
});
it("validates nested report timing contract and enum values", () => {
    expect(() =>
        validateResource("JobStatus", {
            id: identity.user_id,
            call_id: null,
            status: "queued",
            attempts: 0,
            progress: 2,
        }),
    ).toThrow();
    expect(() =>
        validateResource("WorkspaceContext", {
            ...context,
            data_kind: "guessed-production",
        }),
    ).toThrow();
});

it("validates API data without runtime dynamic code evaluation", () => {
    const original = globalThis.Function;
    const blocked = vi.fn(() => {
        throw new Error("Dynamic evaluation prohibited");
    });
    vi.stubGlobal("Function", blocked);
    const value = validateResource("WorkspaceContext", context);
    vi.stubGlobal("Function", original);
    expect(value).toEqual(context);
    expect(blocked).not.toHaveBeenCalled();
});
it("sends filtering and sorting as backend query parameters", async () => {
    const requested: string[] = [];
    const user = await mount("/calls", (path) => {
        requested.push(path);
        return new Response(JSON.stringify(empty));
    });
    await screen.findByRole("heading", { name: "No matching calls" });
    await user.selectOptions(screen.getByLabelText("Status"), "failed");
    await user.type(screen.getByLabelText("Language code"), "fr");
    await user.click(screen.getByRole("button", { name: "Apply language" }));
    await waitFor(() => expect(requested.at(-1)).toContain("language=fr"));
    expect(requested.at(-1)).toContain("status=failed");
});
