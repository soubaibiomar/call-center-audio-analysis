import { expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";
import { AuthProvider } from "./auth";

const identity = {
    tenant_id: "00000000-0000-4000-8000-000000000001",
    user_id: "00000000-0000-4000-8000-000000000002",
    role: "supervisor",
};
function renderApp(route = "/health") {
    const client = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    render(
        <QueryClientProvider client={client}>
            <AuthProvider>
                <MemoryRouter initialEntries={[route]}>
                    <App />
                </MemoryRouter>
            </AuthProvider>
        </QueryClientProvider>,
    );
    return client;
}
it("shows successful health separately from unavailable readiness", async () => {
    vi.stubGlobal(
        "fetch",
        vi.fn((path) =>
            Promise.resolve(
                path === "/health"
                    ? new Response('{"status":"ok"}')
                    : new Response("", { status: 503 }),
            ),
        ),
    );
    renderApp();
    expect(await screen.findByText("Needs attention")).toBeVisible();
    expect(
        screen.getByRole("heading", {
            name: "A clear view of your workspace.",
        }),
    ).toBeVisible();
    expect(screen.getAllByText("Connected")).toHaveLength(2);
});
it("protects a deep link and never fetches private data before connection", async () => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    renderApp("/calls");
    expect(
        await screen.findByLabelText("Workspace access token"),
    ).toBeVisible();
    expect(fetcher).not.toHaveBeenCalled();
});
it("connects using server identity, returns to deep link and clears credentials/cache on logout", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
        "fetch",
        vi
            .fn()
            .mockImplementation((path) =>
                Promise.resolve(
                    new Response(
                        JSON.stringify(
                            path === "/api/v1/me"
                                ? identity
                                : path === "/api/v1/workspace-context"
                                  ? {
                                        data_kind: "synthetic_validation",
                                        live_transport: "not_available",
                                        training_controls: "not_available",
                                    }
                                  : {
                                        items: [],
                                        total: 0,
                                        limit: 20,
                                        offset: 0,
                                    },
                        ),
                    ),
                ),
            ),
    );
    const client = renderApp("/calls");
    await user.type(
        await screen.findByLabelText("Workspace access token"),
        "synthetic-token",
    );
    await user.click(screen.getByRole("button", { name: "Connect securely" }));
    expect(await screen.findByRole("heading", { name: "Calls" })).toBeVisible();
    client.setQueryData(["private-fixture"], "synthetic-value");
    await user.click(
        screen.getByRole("button", { name: "Disconnect workspace" }),
    );
    expect(await screen.findByLabelText("Workspace access token")).toHaveValue(
        "",
    );
    expect(client.getQueryData(["private-fixture"])).toBeUndefined();
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
});
it("shows failed identity verification without rendering protected content", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(new Response("", { status: 401 })),
    );
    renderApp("/models");
    await user.type(
        await screen.findByLabelText("Workspace access token"),
        "invalid-fixture",
    );
    await user.click(screen.getByRole("button", { name: "Connect securely" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
        "expired or is invalid",
    );
    expect(
        screen.queryByRole("heading", { name: "Model lab" }),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText("Workspace access token")).toHaveValue("");
});
it("renders a loading state while server identity is unresolved", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
        "fetch",
        vi.fn(() => new Promise(() => {})),
    );
    renderApp("/connect");
    await user.type(
        screen.getByLabelText("Workspace access token"),
        "fixture-token",
    );
    await user.click(screen.getByRole("button", { name: "Connect securely" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Verifying");
    expect(
        screen.getByRole("button", { name: "Connect securely" }),
    ).toBeDisabled();
});
it("filters navigation and explains empty results", async () => {
    const user = userEvent.setup();
    renderApp("/connect");
    await user.type(
        screen.getByLabelText("Find a workspace page"),
        "missing-page",
    );
    expect(screen.getByRole("status")).toHaveTextContent("No matching pages");
});
it("provides recovery for an unknown route", async () => {
    renderApp("/missing");
    await waitFor(() =>
        expect(
            screen.getByRole("heading", { name: "Page not found" }),
        ).toBeVisible(),
    );
    expect(
        screen.getByRole("link", { name: "Go to system health" }),
    ).toHaveAttribute("href", "/health");
});
