import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Listen on all interfaces so the dev server is reachable inside Docker
    // and from the host machine when port-forwarded.
    host: "0.0.0.0",
    port: 5173,
  },
});
