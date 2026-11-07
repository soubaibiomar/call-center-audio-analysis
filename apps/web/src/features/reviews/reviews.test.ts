import { afterEach, expect, it, vi } from "vitest";
import { ApiError, sendResource } from "../../lib/api/client";
import { validateResource } from "../../lib/api/queries";

const id = "11111111-1111-4111-8111-111111111111";
afterEach(() => vi.unstubAllGlobals());

it("confines writes to local review endpoints and keeps credentials in headers", async () => {
    const fetcher = vi.fn(
        async (_input: RequestInfo | URL, _options?: RequestInit) =>
            new Response(JSON.stringify({ revision: 2 })),
    );
    vi.stubGlobal("fetch", fetcher);
    await sendResource(
        `/api/v1/call-reviews/${id}`,
        "private-test-token",
        "PATCH",
        { expected_revision: 1 },
    );
    const options = fetcher.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(options?.headers).toEqual({
        Authorization: "Bearer private-test-token",
        "Content-Type": "application/json",
    });
    expect(options?.credentials).toBe("omit");
    expect(options?.redirect).toBe("error");
    expect(options?.body).toBe('{"expected_revision":1}');
});
it("blocks unrelated URLs before any request", async () => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    for (const path of [
        "https://example.com/api/v1/call-reviews/" + id,
        "/api/v1/models/train",
        "/api/v1/call-reviews/../me",
    ])
        await expect(
            sendResource(path, "token", "POST", {}),
        ).rejects.toMatchObject({ status: 400 });
    expect(fetcher).not.toHaveBeenCalled();
});
it("handles erasure without trying to parse an empty response", async () => {
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => new Response(null, { status: 204 })),
    );
    await expect(
        sendResource(
            `/api/v1/call-reviews/${id}?expected_revision=2`,
            "token",
            "DELETE",
        ),
    ).resolves.toBeNull();
});
it("reports conflicts without echoing server content", async () => {
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => new Response("private details", { status: 409 })),
    );
    await expect(
        sendResource(`/api/v1/call-reviews/${id}`, "token", "PATCH", {}),
    ).rejects.toEqual(new ApiError(409));
});
it("validates generated Unicode length constraints and rejects forged identity fields", () => {
    const payload = {
        expected_revision: 1,
        segments: [
            {
                segment_index: 0,
                text: "مرحبا bonjour 😀",
                speaker_role: "Agent",
                uncertain: false,
            },
        ],
        qa_override: null,
    };
    expect(validateResource("CorrectionInput", payload)).toEqual(payload);
    expect(() =>
        validateResource("CorrectionInput", { ...payload, reviewer_id: id }),
    ).toThrow();
    expect(() =>
        validateResource("CorrectionInput", {
            ...payload,
            segments: [{ ...payload.segments[0], text: "" }],
        }),
    ).toThrow();
});
