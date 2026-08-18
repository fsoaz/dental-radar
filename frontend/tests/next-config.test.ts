import { describe, expect, it } from "vitest";

import nextConfig from "@/next.config";

describe("frontend security headers", () => {
  it("sets the expected browser protections globally", async () => {
    expect(nextConfig.poweredByHeader).toBe(false);
    expect(nextConfig.headers).toBeTypeOf("function");
    const rules = await nextConfig.headers!();
    const headers = Object.fromEntries(rules[0].headers.map(({ key, value }) => [key, value]));

    expect(rules[0].source).toBe("/(.*)");
    expect(headers["Content-Security-Policy"]).toContain("frame-ancestors 'none'");
    expect(headers["X-Frame-Options"]).toBe("DENY");
    expect(headers["X-Content-Type-Options"]).toBe("nosniff");
    expect(headers["Referrer-Policy"]).toBe("strict-origin-when-cross-origin");
  });
});
