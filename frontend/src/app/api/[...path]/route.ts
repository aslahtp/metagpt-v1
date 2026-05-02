import { NextRequest, NextResponse } from "next/server";

/**
 * Node.js runtime catch-all proxy for /api/* → backend.
 *
 * Unlike the Edge middleware (NextResponse.rewrite), this runs in the Node.js
 * runtime which respects our proxyTimeout config and can sustain connections
 * for the full duration of long-running requests like the pipeline endpoint
 * (~2-3 minutes), without the ~30s Edge timeout cap.
 */
export const runtime = "nodejs";

// Tell Next.js to allow this route handler to run for up to 295 seconds.
// Must match (or be less than) the Cloud Run timeoutSeconds: 300.
export const maxDuration = 295;

// API_URL: server-only override for the proxy. Falls back to NEXT_PUBLIC_API_URL
// so local dev only needs one backend URL in .env (same as client-side api.ts / auth).
const BACKEND_URL =
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

async function proxyRequest(request: NextRequest, params: { path: string[] }) {
  const path = params.path.join("/");
  const { search } = request.nextUrl;
  const destination = `${BACKEND_URL}/api/${path}${search}`;

  // Forward the request body for methods that support it
  const hasBody = !["GET", "HEAD"].includes(request.method);
  const body = hasBody ? await request.arrayBuffer() : undefined;

  // Copy headers, stripping Next.js‑internal ones that would confuse the backend
  const forwardHeaders = new Headers();
  request.headers.forEach((value, key) => {
    if (!["host", "connection", "transfer-encoding"].includes(key.toLowerCase())) {
      forwardHeaders.set(key, value);
    }
  });

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 294_000); // 294s hard limit

  try {
    const backendResponse = await fetch(destination, {
      method: request.method,
      headers: forwardHeaders,
      body: body ? Buffer.from(body) : undefined,
      signal: controller.signal,
      // @ts-expect-error — Node.js fetch supports this to disable compression buffering
      duplex: "half",
    });

    // Stream the response back to the client
    const responseHeaders = new Headers();
    backendResponse.headers.forEach((value, key) => {
      // Skip headers Next.js manages itself
      if (!["content-encoding", "transfer-encoding", "connection"].includes(key.toLowerCase())) {
        responseHeaders.set(key, value);
      }
    });

    return new NextResponse(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: responseHeaders,
    });
  } catch (err: unknown) {
    const isAbort = err instanceof Error && err.name === "AbortError";
    console.error(`[proxy] ${request.method} ${destination} failed:`, err);
    return NextResponse.json(
      { error: isAbort ? "Request timed out" : "Proxy error" },
      { status: isAbort ? 504 : 502 }
    );
  } finally {
    clearTimeout(timeout);
  }
}

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params);
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params);
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params);
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params);
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params);
}

export async function OPTIONS(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params);
}
