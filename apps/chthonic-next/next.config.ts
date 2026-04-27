// @SID: SCRIPT_NEXT_CONFIG_V1
import type { NextConfig } from 'next';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const appRoot = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  typedRoutes: true,
  allowedDevOrigins: ['127.0.0.1', 'localhost'],
  turbopack: {
    root: appRoot,
  },
};

export default nextConfig;
