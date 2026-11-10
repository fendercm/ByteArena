/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Для сервера: next build собирает самодостаточный сервер
  output: "standalone",

  webpack: (config, { isServer }) => {
    if (isServer) {
      config.resolve.alias["msw/browser"] = false;
    }

    return config;
  },
};

export default nextConfig;