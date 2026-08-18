import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ScoringSettingsClient } from "@/components/scoring-settings-client";

const fetchScoringConfig = vi.fn();
const updateScoringConfig = vi.fn();

vi.mock("@/lib/api", () => ({
  ApiRequestError: class ApiRequestError extends Error {
    status: number;
    code: string | null;
    constructor(message: string, status = 400, code: string | null = null) {
      super(message);
      this.status = status;
      this.code = code;
    }
  },
  fetchScoringConfig: (...args: unknown[]) => fetchScoringConfig(...args),
  updateScoringConfig: (...args: unknown[]) => updateScoringConfig(...args),
}));

const sampleConfig = {
  version: 3,
  active: true,
  weights: {
    HIRING: 25,
    ADVERTISING: 30,
    WEBSITE_QUALITY: 15,
    MULTI_LOCATION: 40,
    HIGH_TICKET: 20,
  },
  bands: [
    { name: "COLD", min: 0, max: 50 },
    { name: "WARM", min: 51, max: 100 },
    { name: "HOT", min: 101, max: 150 },
    { name: "IMMEDIATE", min: 151, max: null },
  ],
};

describe("ScoringSettingsClient", () => {
  beforeEach(() => {
    fetchScoringConfig.mockReset();
    updateScoringConfig.mockReset();
    fetchScoringConfig.mockResolvedValue(sampleConfig);
    updateScoringConfig.mockResolvedValue({ ...sampleConfig, version: 4, rescored: 12 });
  });

  afterEach(() => {
    cleanup();
  });

  it("loads active weights into the form", async () => {
    render(<ScoringSettingsClient />);

    expect(await screen.findByDisplayValue("25")).toBeInTheDocument();
    expect(screen.getByText(/Weights \(v3\)/)).toBeInTheDocument();
    expect(fetchScoringConfig).toHaveBeenCalledTimes(1);
  });

  it("saves config and optionally rescores", async () => {
    const user = userEvent.setup();
    render(<ScoringSettingsClient />);
    await screen.findByDisplayValue("25");

    await user.click(screen.getByRole("button", { name: "Save & rescore" }));

    await waitFor(() => {
      expect(updateScoringConfig).toHaveBeenCalledWith(
        expect.objectContaining({
          rescore: true,
          weights: expect.objectContaining({ HIRING: 25 }),
        }),
      );
    });
    expect(await screen.findByText(/Saved version 4; rescored 12 clinics/)).toBeInTheDocument();
  });

  it("surfaces load failures", async () => {
    const { ApiRequestError } = await import("@/lib/api");
    fetchScoringConfig.mockRejectedValue(new ApiRequestError("boom", 500));

    render(<ScoringSettingsClient />);

    expect(await screen.findByRole("alert")).toHaveTextContent("boom");
  });
});
