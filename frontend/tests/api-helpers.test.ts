import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiRequestError,
  buildClinicListQuery,
  updateScoringConfig,
  userFacingFetchError,
} from "@/lib/api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("buildClinicListQuery", () => {
  it("coerces invalid page values to defaults", () => {
    const query = buildClinicListQuery(new URLSearchParams("page=abc&page_size=nope&min_score=x"));
    expect(query.page).toBe(1);
    expect(query.page_size).toBe(20);
    expect(query.min_score).toBeUndefined();
  });

  it("parses valid numeric filters", () => {
    const query = buildClinicListQuery(
      new URLSearchParams("page=3&page_size=50&min_score=10&max_score=90"),
    );
    expect(query.page).toBe(3);
    expect(query.page_size).toBe(50);
    expect(query.min_score).toBe(10);
    expect(query.max_score).toBe(90);
  });
});

describe("userFacingFetchError", () => {
  it("maps network failures", () => {
    expect(userFacingFetchError(new ApiRequestError("x", 0, "NETWORK_ERROR"))).toMatch(
      /Can't reach the service/,
    );
  });

  it("maps server failures", () => {
    expect(userFacingFetchError(new ApiRequestError("internal", 502))).toMatch(
      /Something went wrong/,
    );
  });

  it("keeps clinic validation guidance page-specific", () => {
    expect(userFacingFetchError(new ApiRequestError("specific backend detail", 422, "VALIDATION_ERROR"))).toMatch(
      /reset filters/i,
    );
  });
});

describe("scoring API errors", () => {
  it("preserves the backend validation message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "VALIDATION_ERROR",
              message: "bands leave a gap or overlap between 10 and 50",
              details: null,
            },
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(
      updateScoringConfig({ weights: {}, bands: [], rescore: false }),
    ).rejects.toThrow("bands leave a gap or overlap between 10 and 50");
  });
});
