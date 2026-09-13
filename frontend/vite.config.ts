import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

import { createSeoPluginFromEnv } from "./vite-plugin-seo";

interface PackageJson {
  readonly version: string;
}

const frontendRoot: string = path.dirname(fileURLToPath(import.meta.url));
const packageJson: PackageJson = JSON.parse(
  readFileSync(path.join(frontendRoot, "package.json"), "utf8"),
) as PackageJson;

export default defineConfig(({ mode }) => {
  const env: Record<string, string> = loadEnv(mode, process.cwd(), "");
  const appVersion: string = env.VITE_APP_VERSION?.trim() || packageJson.version;
  return {
    define: {
      __APP_VERSION__: JSON.stringify(appVersion),
    },
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
