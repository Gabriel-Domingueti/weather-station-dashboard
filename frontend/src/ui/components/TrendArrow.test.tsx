import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { TrendArrow } from "./TrendArrow";

describe("TrendArrow", () => {
  it("renders rising arrow", () => {
    render(<TrendArrow trend="rising" />);
    expect(screen.getByText("▲")).toBeInTheDocument();
  });

  it("renders falling arrow", () => {
    render(<TrendArrow trend="falling" />);
    expect(screen.getByText("▼")).toBeInTheDocument();
  });

  it("renders stable arrow", () => {
    render(<TrendArrow trend="stable" />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
