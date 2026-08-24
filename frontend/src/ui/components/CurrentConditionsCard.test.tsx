import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CurrentConditionsCard } from "./CurrentConditionsCard";
import * as hooks from "@/application/hooks/useLatestReading";
import * as trendHooks from "@/application/hooks/useTrend";

// Mock the component dependencies
vi.mock("@/application/hooks/useLatestReading", () => ({
  useLatestReading: vi.fn(),
}));

vi.mock("@/application/hooks/useTrend", () => ({
  useTrend: vi.fn(),
}));

vi.mock("@/ui/components/GaugeDial", () => ({
  GaugeDial: () => <div data-testid="gauge-dial">Gauge</div>,
}));

describe("CurrentConditionsCard", () => {
  it("should show stale badge when data is stale and minutes are not null", () => {
    vi.spyOn(hooks, "useLatestReading").mockReturnValue({
      data: {
        reading: { temperature: 25, humidity: 60, pressure: 1013, timestamp: "2026-08-23" },
        is_stale: true,
        minutes_since_reading: 47,
      },
      isLoading: false,
      isError: false,
    } as any);

    vi.spyOn(trendHooks, "useTrend").mockReturnValue({ data: undefined } as any);

    render(<CurrentConditionsCard />);

    expect(screen.getByText(/Última leitura há 47 min/i)).toBeInTheDocument();
  });

  it("should show generic stale badge when data is stale and minutes are null", () => {
    vi.spyOn(hooks, "useLatestReading").mockReturnValue({
      data: {
        reading: null,
        is_stale: true,
        minutes_since_reading: null,
      },
      isLoading: false,
      isError: false,
    } as any);

    vi.spyOn(trendHooks, "useTrend").mockReturnValue({ data: undefined } as any);

    render(<CurrentConditionsCard />);

    expect(screen.getByText(/Sem dados recentes/i)).toBeInTheDocument();
  });

  it("should not show stale badge when data is not stale", () => {
    vi.spyOn(hooks, "useLatestReading").mockReturnValue({
      data: {
        reading: { temperature: 25, humidity: 60, pressure: 1013, timestamp: "2026-08-23" },
        is_stale: false,
        minutes_since_reading: 5,
      },
      isLoading: false,
      isError: false,
    } as any);

    vi.spyOn(trendHooks, "useTrend").mockReturnValue({ data: undefined } as any);

    render(<CurrentConditionsCard />);

    expect(screen.queryByText(/Sem dados recentes/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Última leitura/i)).not.toBeInTheDocument();
  });
});
