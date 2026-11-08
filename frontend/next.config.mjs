/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // для сервера: next build собирает самодостаточный сервер в .next/standalone (см. Dockerfile.prod)
  output: "standalone",
};

export default nextConfig;
