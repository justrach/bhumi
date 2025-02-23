import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    domains: ['images.bhumi.trilok.ai'],
  },
  webpack: (config) => {
    config.module.rules.push({
      test: /\.(ico|png|jpg|jpeg|gif|svg)$/i,
      type: 'asset/resource',
    })
    return config
  }
};

export default nextConfig;
