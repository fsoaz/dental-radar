import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FilterBar } from "@/components/filter-bar";

const push = vi.fn();
const searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  useSearchParams: () => searchParams,
}));

describe("FilterBar", () => {
  beforeEach(() => {
    push.mockReset();
    for (const key of [...searchParams.keys()]) {
      searchParams.delete(key);
    }
  });

  afterEach(() => {
    cleanup();
  });

  it("updates query when filters are applied", async () => {
    const user = userEvent.setup();
    render(<FilterBar />);

    await user.type(screen.getByLabelText("Search clinics"), "Smile");
    await user.type(screen.getByLabelText("State filter"), "Lisboa");
    await user.click(screen.getByRole("button", { name: "Apply filters" }));

    expect(push).toHaveBeenCalledWith("/clinics?q=Smile&state=Lisboa");
  });

  it("clears filters", async () => {
    const user = userEvent.setup();
    render(<FilterBar />);

    await user.type(screen.getByLabelText("Search clinics"), "test");
    await user.click(screen.getByRole("button", { name: "Clear" }));

    expect(push).toHaveBeenCalledWith("/clinics");
  });
});
