import { describe, expect, it, vi } from "vitest";
import { ApiError, getHealth, getIdentity } from "./client";

const identity = {
    tenant_id: "00000000-0000-4000-8000-000000000001",
    user_id: "00000000-0000-4000-8000-000000000002",
    role: "agent",
};
describe("same-origin API boundary", () => {
    it("uses a bearer header only on the identity request", async () => {
        const fetcher = vi
            .fn()
            .mockResolvedValue(new Response(JSON.stringify(identity)));
        vi.stubGlobal("fetch", fetcher);
        expect(await getIdentity("synthetic-token")).toEqual(identity);
        expect(fetcher).toHaveBeenCalledWith(
            "/api/v1/me",
            expect.objectContaining({
                credentials: "omit",
                redirect: "error",
                cache: "no-store",
                headers: { Authorization: "Bearer synthetic-token" },
            }),
        );
    });
    it.each([401, 403, 503, 500])(
        "maps HTTP %s without reflecting server text or credentials",
        async (status) => {
            vi.stubGlobal(
                "fetch",
                vi
                    .fn()
                    .mockResolvedValue(
                        new Response("private-server-detail", { status }),
                    ),
            );
            const error = await getIdentity("synthetic-token").catch(
                (value: unknown) => value,
            );
            expect(error).toBeInstanceOf(ApiError);
            expect((error as Error).message).not.toContain(
                "private-server-detail",
            );
            expect((error as Error).message).not.toContain("synthetic-token");
        },
    );
    it("rejects malformed identity JSON instead of trusting its role", async () => {
        vi.stubGlobal(
            "fetch",
            vi
                .fn()
                .mockResolvedValue(
                    new Response(JSON.stringify({ ...identity, role: "root" })),
                ),
        );
        await expect(getIdentity("synthetic-token")).rejects.toMatchObject({
            status: 502,
        });
    });
    it("rejects wrong endpoint health status", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue(new Response('{"status":"ok"}')),
        );
        await expect(getHealth("/ready")).rejects.toMatchObject({
            status: 502,
        });
    });
    it("reports a network failure with a retryable user action", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockRejectedValue(new TypeError("secret host")),
        );
        await expect(getHealth("/health")).rejects.toMatchObject({ status: 0 });
    });
    it("health requests carry no bearer token", async () => {
        const fetcher = vi
            .fn()
            .mockResolvedValue(new Response('{"status":"ok"}'));
        vi.stubGlobal("fetch", fetcher);
        await getHealth("/health");
        expect(fetcher).toHaveBeenCalledWith(
            "/health",
            expect.objectContaining({ headers: {} }),
        );
    });
    it("preserves caller cancellation", async () => {
        const controller = new AbortController();
        controller.abort();
        vi.stubGlobal(
            "fetch",
            vi
                .fn()
                .mockRejectedValue(new DOMException("Aborted", "AbortError")),
        );
        await expect(
            getHealth("/health", controller.signal),
        ).rejects.toMatchObject({ name: "AbortError" });
    });
});
