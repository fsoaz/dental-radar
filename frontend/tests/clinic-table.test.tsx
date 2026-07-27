import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ClinicTable } from "@/components/clinic-table";
import type { ClinicListItem } from "@/lib/types";

const clinics: ClinicListItem[] = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    name: "Smile Dental",
    city: "Lisboa",
    state: "Lisboa",
    score: 130,
    priority: "HOT",
    growth_probability: 78,
  },
  {
    id: "22222222-2222-2222-2222-222222222222",
    name: "City Ortho",
    city: "Porto",
    state: "Porto",
    score: 55,
    priority: "WARM",
    growth_probability: 42,
  },
];

describe("ClinicTable", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders clinic rows with score and priority", () => {
    render(<ClinicTable clinics={clinics} />);

    expect(screen.getByRole("link", { name: "Smile Dental" })).toHaveAttribute(
      "href",
      "/clinics/11111111-1111-1111-1111-111111111111",
    );
    expect(screen.getByText("Lisboa")).toBeInTheDocument();
    expect(screen.getByText("130")).toBeInTheDocument();
    expect(screen.getByText("78%")).toBeInTheDocument();
    expect(screen.getByText("Hot")).toBeInTheDocument();
    expect(screen.getByText("City Ortho")).toBeInTheDocument();
  });

  it("shows empty state when no clinics", () => {
    render(<ClinicTable clinics={[]} />);
    expect(screen.getByText("No clinics match your filters")).toBeInTheDocument();
  });

  it("preserves list query on clinic links", () => {
    render(<ClinicTable clinics={clinics} listQuery="priority=HOT&page=3" />);

    expect(screen.getByRole("link", { name: "Smile Dental" })).toHaveAttribute(
      "href",
      "/clinics/11111111-1111-1111-1111-111111111111?priority=HOT&page=3",
    );
  });
});
