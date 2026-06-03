import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep tracing inside frontend/ (avoids parent lockfile confusion)
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
