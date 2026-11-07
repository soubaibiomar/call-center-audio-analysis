import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HashRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";
import { AuthProvider } from "./auth";
import "./workspace.css";
import "../features/workspace/features.css";

const client = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: true } },
});
const root = document.getElementById("root");
if (!root) throw new Error("Workspace root is missing");
createRoot(root).render(
    <StrictMode>
        <QueryClientProvider client={client}>
            <AuthProvider>
                <HashRouter>
                    <App />
                </HashRouter>
            </AuthProvider>
        </QueryClientProvider>
    </StrictMode>,
);
