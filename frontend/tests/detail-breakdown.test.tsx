import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AIBreakdown } from "@/components/ai-breakdown";
import { ScoreBreakdown } from "@/components/score-breakdown";

describe("Clinic detail breakdown", () => {
  it("renders AI enrichment scores and explanation", () => {
    render(
      <AIBreakdown
        enrichment={{
          growth_probability: 78,
          technology_maturity: 65,
          marketing_sophistication: 72,
          expansion_probability: 80,
          explanation: "Active implant marketing and two locations.",
        }}
      />,
    );

    expect(screen.getByText("AI enrichment")).toBeInTheDocument();
    expect(screen.getByText("78%")).toBeInTheDocument();
    expect(screen.getByText("65%")).toBeInTheDocument();
    expect(screen.getByText("Active implant marketing and two locations.")).toBeInTheDocument();
  });

  it("renders rule-based score breakdown", () => {
    render(
      <ScoreBreakdown
        score={{
          total: 130,
          priority: "HOT",
          breakdown: {
            MULTI_LOCATION: 40,
            ADVERTISING: 30,
            HIRING: 25,
            HIGH_TICKET: 20,
            WEBSITE_QUALITY: 15,
          },
          config_version: 1,
        }}
      />,
    );

    expect(screen.getByText("Rule-based score")).toBeInTheDocument();
    expect(screen.getByText("130")).toBeInTheDocument();
    expect(screen.getByText("Hot")).toBeInTheDocument();
    expect(screen.getByText("+40")).toBeInTheDocument();
  });
});
