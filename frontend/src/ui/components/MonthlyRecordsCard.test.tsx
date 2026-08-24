import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MonthlyRecordsCard } from "./MonthlyRecordsCard";
import * as hooks from "@/application/hooks/useMonthlyRecords";

vi.mock("@/application/hooks/useMonthlyRecords", () => ({
  useMonthlyRecords: vi.fn(),
}));

describe("MonthlyRecordsCard", () => {
  it("shows loading state", () => {
    vi.spyOn(hooks, "useMonthlyRecords").mockReturnValue({
      isLoading: true,
      data: undefined,
      isError: false,
    } as any);

    render(<MonthlyRecordsCard />);
    expect(screen.getByText(/Carregando recordes/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    vi.spyOn(hooks, "useMonthlyRecords").mockReturnValue({
      isLoading: false,
      data: undefined,
      isError: true,
    } as any);

    render(<MonthlyRecordsCard />);
    expect(screen.getByText(/Sem recordes/i)).toBeInTheDocument();
  });

  it("shows no data message when all records are null", () => {
    vi.spyOn(hooks, "useMonthlyRecords").mockReturnValue({
      isLoading: false,
      data: {
        month: "2026-08",
        temperature: { max_value: null, max_date: null, min_value: null, min_date: null },
        humidity: { max_value: null, max_date: null, min_value: null, min_date: null },
        pressure: { max_value: null, max_date: null, min_value: null, min_date: null },
      },
      isError: false,
    } as any);

    render(<MonthlyRecordsCard />);
    // Checking all metrics show "sem dados ainda"
    expect(screen.getAllByText(/sem dados ainda/i).length).toBe(3);
  });

  it("shows actual records when available", () => {
    vi.spyOn(hooks, "useMonthlyRecords").mockReturnValue({
      isLoading: false,
      data: {
        month: "2026-08",
        temperature: { max_value: 35.5, max_date: "2026-08-15", min_value: 12.0, min_date: "2026-08-01" },
        humidity: { max_value: 90, max_date: "2026-08-20", min_value: 40, min_date: "2026-08-05" },
        pressure: { max_value: 1020, max_date: "2026-08-10", min_value: 1005, min_date: "2026-08-11" },
      },
      isError: false,
    } as any);

    render(<MonthlyRecordsCard />);
    expect(screen.getByText(/35.5°C em 15\/08\/2026/)).toBeInTheDocument();
    expect(screen.getByText(/12°C em 01\/08\/2026/)).toBeInTheDocument();
  });
});
