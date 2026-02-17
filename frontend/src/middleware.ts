import { NextRequest, NextResponse } from "next/server";

/**
 * Middleware to proxy /api/* requests to the backend.
 *
 * Uses the runtime env var API_URL (NOT NEXT_PUBLIC_ so it isn't
 * replaced at build time and can be set per-environment).
 */
export function middleware(request: NextRequest) {
  const backendUrl = process.env.API_URL || "http://localhost:8000";

  const { pathname, search } = request.nextUrl;
  const destination = new URL(pathname + search, backendUrl);

  return NextResponse.rewrite(destination);
}

export const config = {
  matcher: "/api/:path*",
};
