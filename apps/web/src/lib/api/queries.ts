import { useQuery } from "@tanstack/react-query";
import * as validators from "./validators.generated.mjs";
import { useSession } from "../../app/auth";
import { ApiError, getResource } from "./client";

export function validateResource<T>(name: string, data: unknown): T {
    if (!Object.hasOwn(validators, name)) throw new ApiError(502);
    const validate = validators[name as keyof typeof validators];
    if (!validate(data)) throw new ApiError(502);
    return data as T;
}
export function useApiQuery<T>(
    path: string,
    schema: string,
    enabled = true,
    interval?: number,
    stable = false,
) {
    const { accessToken, generation } = useSession();
    return useQuery({
        queryKey: ["workspace", generation, path],
        queryFn: async ({ signal }) =>
            validateResource<T>(
                schema,
                await getResource<unknown>(path, accessToken, signal),
            ),
        enabled: Boolean(accessToken) && enabled,
        staleTime: stable ? Infinity : 10000,
        refetchOnWindowFocus: !stable,
        retry: false,
        refetchInterval: interval ?? false,
    });
}
