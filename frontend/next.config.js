/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  experimental: {
    // Allow proxied requests up to 295s (just under Cloud Run's 300s timeout).
    // This is needed because the pipeline endpoint can take ~2-3 minutes to
    // complete. Without this, Next.js's internal proxy drops the connection
    // after ~30s with ECONNRESET even though Cloud Run is configured for 300s.
    proxyTimeout: 295_000,
  },
};

module.exports = nextConfig;
