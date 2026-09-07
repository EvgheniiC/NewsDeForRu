import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

import { createSeoPluginFromEnv } from "./vite-plugin-seo";

export default defineConfig(({ mode }) => {
  const env: Record<string, string> = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [react(), createSeoPluginFromEnv(env, mode === "production")],
    server: {
      port: 5173,
      // Listen on all interfaces so http://127.0.0.1:5173 works like http://localhost:5173 on Windows.
      host: true,
    },
    test: {
      environment: "jsdom",
      include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    },
  };
});
