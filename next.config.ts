import type { NextConfig } from "next";

const API_URL = process.env.API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // Proxy all /api/* requests to the FastAPI backend.
  // This keeps the frontend code unchanged — it still calls /api/jobs etc.
  // and Next.js transparently forwards them to the Python server.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
