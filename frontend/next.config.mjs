/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Для сервера: next build собирает самодостаточный сервер
  output: "standalone",

  // Для локальной проверки без Caddy. В Docker /api маршрутизирует Caddy.
  async rewrites() {
    const backend = process.env.API_PROXY_TARGET;
    return backend ? [{ source: "/api/:path*", destination: `${backend}/:path*` }] : [];
  },

  webpack: (config, { isServer }) => {
    if (isServer) {
      config.resolve.alias["msw/browser"] = false;
    }

    return config;
  },
};

export default nextConfig;
