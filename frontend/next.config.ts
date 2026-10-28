import type { NextConfig } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
// Google serves the profile pictures of signed-in visitors from this host.
const GOOGLE_PHOTOS = "https://lh3.googleusercontent.com";
const isProduction = process.env.NODE_ENV === "production";

/**
 * Next.js writes a few inline bootstrap scripts, so scripts need 'unsafe-inline' (and, in
 * development only, 'unsafe-eval' for hot reload). Everything else is locked to this site and
 * the API. The live browser view of an agent is an https frame from TinyFish, so frames may
 * load any https page; the frame itself is sandboxed in the component.
 */
const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isProduction ? "" : " 'unsafe-eval'"}`,
  "style-src 'self' 'unsafe-inline'",
  `img-src 'self' data: blob: ${GOOGLE_PHOTOS}`,
  "font-src 'self'",
  `connect-src 'self' ${API_URL}`,
  "frame-src https:",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join("; ");

const config: NextConfig = {
  reactStrictMode: true,
  images: { remotePatterns: [{ protocol: "https", hostname: "lh3.googleusercontent.com" }] },
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: CONTENT_SECURITY_POLICY },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default config;
