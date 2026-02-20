import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  turbopack: {
    root: frontendRoot,
  },
  // API routes proxy to existing Bun server
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:4000/api/:path*',
      },
    ];
  },
  // Disable SSG page generation for pages with client-side only features
  generateBuildId: async () => {
    return 'mas-mcp-dashboard-' + Date.now();
  },
};

export default nextConfig;
