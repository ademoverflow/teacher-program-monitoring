import { fileURLToPath, URL } from "node:url";
import tailwindcss from "@tailwindcss/vite";
import { devtools } from "@tanstack/devtools-vite";
import viteReact from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Inside Docker Compose the API is reachable through the service name `core`.
// When running Vite directly on the host, point it at the published port:
//   API_PROXY_TARGET=http://localhost:12109 pnpm dev
const apiProxyTarget = process.env.API_PROXY_TARGET ?? "http://core:80";

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [devtools(), viteReact(), tailwindcss()],
	resolve: {
		alias: {
			"@": fileURLToPath(new URL("./src", import.meta.url)),
		},
	},
	server: {
		// Same-origin `/api/*` calls are forwarded to the core API: no CORS, no
		// absolute URL (and no LAN IP) needed in the frontend.
		proxy: {
			"/api": {
				target: apiProxyTarget,
				changeOrigin: true,
			},
		},
	},
	test: {
		environment: "jsdom",
		setupFiles: ["./src/test/setup.ts"],
	},
});
