/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    const target = process.env.INTERNAL_API_URL || "http://localhost:8000/api/v1";
    return [
      // Browser hits /api/v1/* on its own origin; Next proxies to the FastAPI service.
      // This keeps the session cookie same-origin so middleware can gate on it.
      { source: "/api/v1/:path*", destination: `${target}/:path*` },
    ];
  },
};

export default nextConfig;
