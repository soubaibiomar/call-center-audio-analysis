import {
    createContext,
    useContext,
    useRef,
    useState,
    type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getIdentity } from "../lib/api/client";

function useSessionState() {
    const [token, setToken] = useState("");
    const [generation, setGeneration] = useState(0);
    const client = useQueryClient();
    const sequence = useRef(0);
    const identity = useQuery({
        queryKey: ["identity", generation],
        queryFn: ({ signal }) => getIdentity(token, signal),
        enabled: Boolean(token),
        retry: false,
        staleTime: 0,
        gcTime: 0,
        refetchInterval: token ? 60000 : false,
    });
    function clear() {
        sequence.current += 1;
        setToken("");
        void client.cancelQueries();
        client.clear();
    }
    function connect(value: string) {
        clear();
        setGeneration(sequence.current);
        setToken(value.trim());
    }
    return {
        identity,
        tokenPresent: Boolean(token),
        accessToken: token,
        generation,
        connect,
        clear,
    };
}

const Session = createContext<ReturnType<typeof useSessionState> | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
    return (
        <Session.Provider value={useSessionState()}>
            {children}
        </Session.Provider>
    );
}
export function useSession() {
    const session = useContext(Session);
    if (!session) throw new Error("AuthProvider is required");
    return session;
}
