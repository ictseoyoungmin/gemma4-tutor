import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || "http://api:8000";

  return {
    plugins: [react()],
    server: {
      allowedHosts: [
        "injuries-turn-ebooks-operational.trycloudflare.com",
      ],
      port: 5173,
      proxy: {
        "/v1": {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
