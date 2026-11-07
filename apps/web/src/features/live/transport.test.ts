import { afterEach, expect, it, vi } from "vitest";
import { BrowserCall, liveError } from "./transport";
import { ApiError } from "../../lib/api/client";
import { validateResource } from "../../lib/api/queries";
import type { LiveSessionView } from "../../lib/api/generated";

const room: LiveSessionView = {
    id: "11111111-1111-4111-8111-111111111111",
    initiator_user_id: "22222222-2222-4222-8222-222222222222",
    participants: [],
    consent_revision: 0,
    capture_allowed: false,
    remaining_seconds: 600,
};
afterEach(() => vi.unstubAllGlobals());

it("reports permission denial and clears the invitation without starting RTC", async () => {
    vi.stubGlobal("isSecureContext", true);
    vi.stubGlobal("navigator", {
        mediaDevices: {
            getUserMedia: vi
                .fn()
                .mockRejectedValue(
                    new DOMException("denied", "NotAllowedError"),
                ),
        },
    });
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => new Response(null, { status: 204 })),
    );
    const remote = document.createElement("audio");
    remote.pause = vi.fn();
    const update = vi.fn();
    const call = new BrowserCall(
        "private-test-token",
        room.initiator_user_id,
        remote,
        update,
    );
    await expect(call.connect(room, false)).rejects.toThrow(
        "Microphone permission was denied",
    );
    expect(remote.pause).toHaveBeenCalled();
    expect(update).toHaveBeenLastCalledWith(
        expect.objectContaining({ connection: "ended", session: null }),
    );
});
it("releases microphone tracks if permission resolves after the user has ended", async () => {
    vi.stubGlobal("isSecureContext", true);
    let grant: (value: MediaStream) => void = () => {};
    const permission = new Promise<MediaStream>((resolve) => {
        grant = resolve;
    });
    vi.stubGlobal("navigator", {
        mediaDevices: { getUserMedia: vi.fn(() => permission) },
    });
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => new Response(null, { status: 204 })),
    );
    const track = { stop: vi.fn() };
    const remote = document.createElement("audio");
    remote.pause = vi.fn();
    const call = new BrowserCall(
        "private-test-token",
        room.initiator_user_id,
        remote,
        vi.fn(),
    );
    const connecting = call.connect(room, false);
    await call.stop();
    grant({ getTracks: () => [track] } as unknown as MediaStream);
    await connecting;
    expect(track.stop).toHaveBeenCalledOnce();
    expect(remote.srcObject).toBeNull();
});
it("validates typed live events and rejects binary-shaped or forged event kinds", () => {
    expect(
        validateResource("LiveEvent", { type: "session", session: room }),
    ).toEqual({ type: "session", session: room });
    expect(() =>
        validateResource("LiveEvent", { type: "audio", bytes: "untrusted" }),
    ).toThrow();
    expect(() =>
        validateResource("LiveEvent", {
            type: "transcript",
            segments: [
                { start_seconds: -1, end_seconds: 1, text: "bad timing" },
            ],
        }),
    ).toThrow();
});
it("provides live-specific conflict and admission errors", () => {
    expect(liveError(new ApiError(409))).toContain(
        "Refresh the call invitations",
    );
    expect(liveError(new ApiError(403))).toContain("not authorized");
    expect(liveError(new ApiError(429))).toContain("Analysis has stopped");
});
