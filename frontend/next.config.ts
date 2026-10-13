import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Permite conexiones de desarrollo/HMR desde cualquier dispositivo en la red local y túneles Cloudflare
  allowedDevOrigins: [
    "localhost",
    "127.0.0.1",
    "*.local",
    "192.168.*.*",
    "gruamb.vial25.dpdns.org",
    "*.dpdns.org",
    "*.vial25.dpdns.org",
  ],
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://127.0.0.1:8000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
