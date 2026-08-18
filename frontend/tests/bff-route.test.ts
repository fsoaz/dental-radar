import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET, POST } from "@/app/api/backend/[...path]/route";

const context = (path: string[]) => ({ params: Promise.resolve({ path }) });

describe("backend BFF route", () => {
  beforeEach(() => {
    process.env.API_URL = "http://api:8000/api/v1";
    process.env.API_KEY = "server-secret"; // gitleaks:allow
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    delete process.env.API_URL;
    delete process.env.API_KEY;
  });

  it("proxies queries without exposing the API key on reads", async () => {
    const upstream = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        headers: { "Content-Type": "application/json", "X-Internal": "hidden" },
      }),
    );
    vi.stubGlobal("fetch", upstream);

    const response = await GET(
      new NextRequest("http://frontend/api/backend/clinics?page=2", {
        headers: { "X-API-Key": "attacker-key" },
      }),
      context(["clinics"]),
    );

    expect(upstream).toHaveBeenCalledWith(
      "http://api:8000/api/v1/clinics?page=2",
      expect.objectContaining({ method: "GET" }),
    );
    const headers = upstream.mock.calls[0][1].headers as Headers;
    expect(headers.has("X-API-Key")).toBe(false);
    expect(response.headers.get("x-internal")).toBeNull();
  });

  it("injects only the server key on mutations and forwards Retry-After", async () => {
    const upstream = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { code: "RATE_LIMITED" } }), {
        status: 429,
        headers: { "Content-Type": "application/json", "Retry-After": "27" },
      }),
    );
    vi.stubGlobal("fetch", upstream);

    const response = await POST(
      new NextRequest("http://frontend/api/backend/clinics/discover", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": "attacker-key" },
        body: JSON.stringify({ query: "dentist" }),
      }),
      context(["clinics", "discover"]),
    );

    const headers = upstream.mock.calls[0][1].headers as Headers;
    expect(headers.get("X-API-Key")).toBe("server-secret"); // gitleaks:allow
    expect(response.status).toBe(429);
    expect(response.headers.get("Retry-After")).toBe("27");
  });

  it("fails closed when the server key is missing", async () => {
    delete process.env.API_KEY;
    const upstream = vi.fn();
    vi.stubGlobal("fetch", upstream);

    const response = await POST(
      new NextRequest("http://frontend/api/backend/scoring-config", { method: "POST" }),
      context(["scoring-config"]),
    );

    expect(response.status).toBe(503);
    expect(upstream).not.toHaveBeenCalled();
  });
});
