import type { Health, Identity } from "./generated";

export class ApiError extends Error {
    constructor(public readonly status: number) {
        super(
            status === 401
                ? "Your access has expired or is invalid. Connect again."
                : status === 403
                  ? "This account has not been enabled for this workspace."
                  : status === 409
                    ? "This review changed. Refresh it and reapply your corrections."
                    : status === 422
                      ? "Check the correction, supporting audio range and recording match."
                      : status === 404
                        ? "This item is unavailable or its retention period has ended."
                        : status === 503
                          ? "The service is not ready. Check the local API configuration."
                          : status === 0
                            ? "Cannot reach the local API. Check that it is running and try again."
                            : "The API returned an unexpected response. Try again.",
        );
        this.name = "ApiError";
    }
}

async function get(
    path: string,
    signal?: AbortSignal,
    token?: string,
): Promise<unknown> {
    let response: Response;
    try {
        response = await fetch(path, {
            signal: AbortSignal.any([
                AbortSignal.timeout(8000),
                ...(signal ? [signal] : []),
            ]),
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            cache: "no-store",
            credentials: "omit",
            redirect: "error",
        });
    } catch (error) {
        if (signal?.aborted) throw error;
        throw new ApiError(0);
    }
    if (!response.ok) throw new ApiError(response.status);
    try {
        return await response.json();
    } catch {
        throw new ApiError(502);
    }
}

export async function getResource<T>(
    path: string,
    token: string,
    signal?: AbortSignal,
): Promise<T> {
    if (
        !/^\/api\/v1\/(?:dashboard(?:\/activity)?|workspace-context|model-versions|calls(?:\/[0-9a-f-]{36}\/(?:report|review))?|call-reviews\/[0-9a-f-]{36}\/history|call-review-dataset|jobs\/[0-9a-f-]{36}|live\/(?:config|peers|sessions))(?:\?[^#]*)?$/i.test(
            path,
        ) ||
        !token
    )
        throw new ApiError(400);
    return (await get(path, signal, token)) as T;
}

export async function sendResource(
    path: string,
    token: string,
    method: "POST" | "PATCH" | "DELETE",
    body?: unknown,
): Promise<unknown> {
    if (
        !token ||
        !/^\/api\/v1\/(?:calls\/[0-9a-f-]{36}\/reviews|call-reviews\/[0-9a-f-]{36}(?:\/(?:decisions|consent))?|live\/sessions(?:\/[0-9a-f-]{36}(?:\/(?:tickets|consent|finalize))?)?)(?:\?expected_revision=\d+)?$/i.test(
            path,
        )
    )
        throw new ApiError(400);
    let response: Response;
    try {
        response = await fetch(path, {
            method,
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
            body: body === undefined ? undefined : JSON.stringify(body),
            signal: AbortSignal.timeout(8000),
            credentials: "omit",
            redirect: "error",
            cache: "no-store",
        });
    } catch {
        throw new ApiError(0);
    }
    if (!response.ok) throw new ApiError(response.status);
    if (response.status === 204) return null;
    try {
        return await response.json();
    } catch {
        throw new ApiError(502);
    }
}

function object(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

export async function getHealth(
    path: "/health" | "/ready",
    signal?: AbortSignal,
): Promise<Health> {
    const data = await get(path, signal);
    const expected: Health["status"] = path === "/health" ? "ok" : "ready";
    if (!object(data) || data.status !== expected) throw new ApiError(502);
    return { status: expected };
}

export async function getIdentity(
    token: string,
    signal?: AbortSignal,
): Promise<Identity> {
    const data = await get("/api/v1/me", signal, token);
    const uuid =
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (
        !object(data) ||
        typeof data.user_id !== "string" ||
        !uuid.test(data.user_id) ||
        typeof data.tenant_id !== "string" ||
        !uuid.test(data.tenant_id) ||
        !["agent", "supervisor", "admin"].includes(String(data.role))
    )
        throw new ApiError(502);
    return {
        user_id: data.user_id,
        tenant_id: data.tenant_id,
        role: data.role as Identity["role"],
    };
}
