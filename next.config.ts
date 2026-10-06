import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /** Documented for Next; vinext ignores this but capture uses `/api/ingest` (API exempt from 308). */
  skipTrailingSlashRedirect: true,
  async redirects() {
    return [
      {
        source: "/entries/:id",
        destination: "/e/:id",
        permanent: true,
      },
    ];
  },
  // www → apex handled in middleware.ts (301 + canonical host)
  async headers() {
    const iconCache = "public, max-age=86400";
    const iconPaths = [
      "/favicon.ico",
      "/favicon.svg",
      "/favicon-16.png",
      "/favicon-32.png",
      "/favicon-48.png",
      "/apple-touch-icon.png",
      "/icon-192.png",
      "/icon-192-maskable.png",
      "/icon-512.png",
      "/icon-512-maskable.png",
      "/site.webmanifest",
    ];
    return [
      {
        source: "/assets/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
      ...iconPaths.map((source) => ({
        source,
        headers: [
          { key: "Cache-Control", value: iconCache },
        ],
      })),
    ];
  },
};

export default nextConfig;
