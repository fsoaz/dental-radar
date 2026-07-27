import { describe, expect, it } from "vitest";

import { ApiRequestError, buildClinicListQuery, userFacingFetchError } from "@/lib/api";

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
});
