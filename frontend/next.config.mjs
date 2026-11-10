/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Необязательно: локальный запуск без Caddy. В Docker запросы направляет Caddy.
  async rewrites() {
    const backend = process.env.API_PROXY_TARGET;
    return backend ? [{ source: "/api/:path*", destination: `${backend}/:path*` }] : [];
  },
};

export default nextConfig;
