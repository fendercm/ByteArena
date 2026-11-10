/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // для сервера: next build собирает самодостаточный сервер в .next/standalone (см. Dockerfile.prod)
  output: "standalone",
  // Для локальной проверки без Caddy. В Docker /api маршрутизирует Caddy.
  async rewrites() {
    const backend = process.env.API_PROXY_TARGET;
    return backend ? [{ source: "/api/:path*", destination: `${backend}/:path*` }] : [];
  },
};

export default nextConfig;
