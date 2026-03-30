import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Webpack used instead of Turbopack (--webpack flag in package.json scripts)
  // to avoid Next.js 16.2.1 Turbopack RocksDB SST cache corruption.
  webpack: (config, { dev }) => {
    if (dev) {
      // Disable webpack's pack-file cache in dev — prevents ENOENT errors
      // on fresh .next directories when pack.gz files don't exist yet.
      config.cache = false;
    }
    return config;
  },
};

export default nextConfig;
