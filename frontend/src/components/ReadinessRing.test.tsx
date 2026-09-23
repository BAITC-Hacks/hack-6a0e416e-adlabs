import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReadinessRing } from "./ReadinessRing";


describe("ReadinessRing", () => {
  it("clamps values and exposes an accessible label", () => {
    render(<ReadinessRing value={118} label="Readiness" />);

    expect(screen.getByRole("img", { name: "Readiness: 100%" })).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });
});
