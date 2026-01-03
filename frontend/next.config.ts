import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/static/:path*',
        destination: 'http://127.0.0.1:8000/static/:path*',
      },
      {
        source: '/vnc/:path*',
        destination: 'http://127.0.0.1:6080/:path*',
      },
      {
        source: '/websockify',
        destination: 'http://127.0.0.1:6080/websockify',
      },
    ];
  },
};

export default nextConfig;
