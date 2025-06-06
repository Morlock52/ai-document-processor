/** @type {import('next').NextConfig} */

const nextConfig = {
  output: 'standalone',
  
  // Proxy API requests to backend
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://api:8000/api/v1/:path*',
      },
    ];
  },
  
  // Allow external images if needed
  images: {
    domains: ['localhost'],
  },
};

module.exports = nextConfig;