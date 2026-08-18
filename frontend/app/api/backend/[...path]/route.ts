import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ path: string[] }> };

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const FORWARDED_RESPONSE_HEADERS = ["content-type", "retry-after", "x-request-id"];

function configurationError(message: string): Response {
  return Response.json(
    { error: { code: "BFF_NOT_CONFIGURED", message, details: null } },
    { status: 503 },
  );
}

async function proxy(request: NextRequest, context: RouteContext): Promise<Response> {
  const apiUrl = process.env.API_URL?.trim().replace(/\/$/, "");
  if (!apiUrl) return configurationError("The API proxy is not configured");

  let base: URL;
  try {
    base = new URL(apiUrl);
  } catch {
    return configurationError("The API proxy URL is invalid");
  }
  if (!new Set(["http:", "https:"]).has(base.protocol)) {
    return configurationError("The API proxy URL must use HTTP or HTTPS");
  }

  const { path } = await context.params;
  if (!path.length || path.some((part) => !part || part === "." || part === ".." || /[\\/]/.test(part))) {
    return Response.json(
      { error: { code: "INVALID_PROXY_PATH", message: "Invalid API path", details: null } },
      { status: 400 },
    );
  }

  const query = new URL(request.url).search;
  const target = `${base.toString().replace(/\/$/, "")}/${path.map(encodeURIComponent).join("/")}${query}`;
  const headers = new Headers({ Accept: request.headers.get("accept") ?? "application/json" });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  const requestId = request.headers.get("x-request-id");
  if (requestId) headers.set("X-Request-ID", requestId);

  if (MUTATING_METHODS.has(request.method)) {
    const apiKey = process.env.API_KEY?.trim();
    if (!apiKey) return configurationError("The operator API key is not configured");
    headers.set("X-API-Key", apiKey);
  }

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: MUTATING_METHODS.has(request.method) ? await request.arrayBuffer() : undefined,
      cache: "no-store",
      redirect: "manual",
    });
    const responseHeaders = new Headers({ "Cache-Control": "no-store" });
    for (const name of FORWARDED_RESPONSE_HEADERS) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return Response.json(
      {
        error: {
          code: "UPSTREAM_UNAVAILABLE",
          message: "Can't reach the API service",
          details: null,
        },
      },
      { status: 502 },
    );
  }
}

export function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function HEAD(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function PUT(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function PATCH(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function DELETE(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}
