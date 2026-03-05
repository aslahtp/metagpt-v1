import { NextRequest, NextResponse } from "next/server";

/**
 * Middleware for non-API routes (auth guards, redirects, etc.)
 *
 * NOTE: /api/* routes are intentionally excluded from this middleware.
 * They are handled by src/app/api/[...path]/route.ts which runs on the
 * Node.js runtime and supports long-running proxy connections (e.g. the
 * pipeline endpoint can take ~2-3 minutes). The Edge runtime used here
 * would time out those requests after ~30s.
 */
export function middleware(request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  // Explicitly exclude /api/* so the App Router route handler takes over
  matcher: "/((?!api/).*)",
};

