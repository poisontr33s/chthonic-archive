/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Bun-native runtime - no Node polyfills needed
  experimental: {
    // Enable Bun compatibility
  },
  // Force dynamic rendering for all pages (skip SSG pre-rendering)
  // This avoids Next.js 16 SSG issues with client-only components
  output: undefined,
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

module.exports = nextConfig;
