import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  async rewrites() {
    const backend = (process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL || (process.env.NODE_ENV === 'production' ? 'https://buscom-backend.onrender.com' : 'http://127.0.0.1:8000')).replace(/\/$/, '');
    return [{ source: '/api/:path*', destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
