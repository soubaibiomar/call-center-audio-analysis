import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

const apiPort = Number(process.env.PROJECT28_DEV_API_PORT || 8781);
if (!Number.isInteger(apiPort) || apiPort < 1 || apiPort > 65535)
    throw new Error("Invalid local API port");
const apiTarget = `http://127.0.0.1:${apiPort}`;

export default defineConfig({
    root: fileURLToPath(new URL("./workspace", import.meta.url)),
    base: "/workspace/",
    plugins: [tailwindcss()],
    build: { outDir: "../dist-workspace", emptyOutDir: true },
    server: {
        host: "127.0.0.1",
        port: 8783,
        strictPort: true,
        fs: { allow: [fileURLToPath(new URL(".", import.meta.url))] },
        proxy: {
            "/api": apiTarget,
            "/health": apiTarget,
            "/ready": apiTarget,
        },
    },
});
