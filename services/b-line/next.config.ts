import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // For Docker builds
  reactStrictMode: true,
};

export default nextConfig;
