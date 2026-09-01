import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AgroIndicesCard } from "./AgroIndicesCard";
import * as useAgroIndicesModule from "@/application/hooks/useAgroIndices";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

describe("AgroIndicesCard", () => {
  const renderComponent = () =>
    render(
      <QueryClientProvider client={queryClient}>
        <AgroIndicesCard />
      </QueryClientProvider>
    );

  it("should show provisional warning regardless of data state", () => {
    vi.spyOn(useAgroIndicesModule, "useAgroIndices").mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as any);

    renderComponent();
    expect(
      screen.getByText(/Parâmetros de cálculo.*são provisórios/i)
    ).toBeInTheDocument();
  });

  it("should show 'sem dados de índices ainda' when data is empty", () => {
    vi.spyOn(useAgroIndicesModule, "useAgroIndices").mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    } as any);

    renderComponent();
    expect(screen.getByText(/sem dados de índices ainda/i)).toBeInTheDocument();
  });

  it("should show GD acumulado and DMF hours of the most recent day", () => {
    vi.spyOn(useAgroIndicesModule, "useAgroIndices").mockReturnValue({
      data: [
        { date: "2026-08-01", gd: 10, gd_acumulado: 10, dmf_hours: 1.5 },
        { date: "2026-08-02", gd: 15, gd_acumulado: 25, dmf_hours: 3.2 },
      ],
      isLoading: false,
      isError: false,
    } as any);

    renderComponent();
    
    // Most recent day is the last element
    expect(screen.getByText("25.0")).toBeInTheDocument(); // GD acumulado
    expect(screen.getByText("3.2h")).toBeInTheDocument(); // DMF
  });
});
