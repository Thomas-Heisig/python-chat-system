import { defineConfig } from "vite";

function parseAllowedHosts(rawValue: string | undefined): true | string[] {
  if (!rawValue) {
    return true;
  }
  const hosts = rawValue
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
  return hosts.length > 0 ? hosts : true;
}

export default defineConfig(() => {
  const frontendPort = Number(process.env.FRONTEND_PORT ?? 5173);
  const backendTarget = process.env.VITE_DEV_BACKEND_TARGET ?? "http://127.0.0.1:8000";
  const frontendHost = process.env.FRONTEND_HOST ?? "0.0.0.0";

  return {
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: "./src/test/setup.ts",
    },
    server: {
      host: frontendHost,
      port: Number.isFinite(frontendPort) ? frontendPort : 5173,
      strictPort: true,
      allowedHosts: parseAllowedHosts(process.env.VITE_ALLOWED_HOSTS),
      proxy: {
        "/api": {
          target: backendTarget,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: frontendHost,
      port: Number.isFinite(frontendPort) ? frontendPort : 5173,
      strictPort: true,
      allowedHosts: parseAllowedHosts(process.env.VITE_ALLOWED_HOSTS),
    },
  };
});
