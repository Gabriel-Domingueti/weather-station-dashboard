import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { PhytosanitaryAlertsCard } from "./PhytosanitaryAlertsCard";
import * as usePhytosanitaryAlertsModule from "@/application/hooks/usePhytosanitaryAlerts";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

describe("PhytosanitaryAlertsCard", () => {
  const renderComponent = () =>
    render(
      <QueryClientProvider client={queryClient}>
        <PhytosanitaryAlertsCard />
      </QueryClientProvider>
    );

  it("should render empty message when there are no alerts", () => {
    vi.spyOn(usePhytosanitaryAlertsModule, "usePhytosanitaryAlerts").mockReturnValue({
      data: {
        reference_date: null,
        region: "Sul de Minas Gerais (Varginha)",
        gd_acumulado: 0,
        dmf_last_24h: 0,
        dmf_last_48h: 0,
        phenology: { nodes_per_branch: 0, leafiness_pct: 0 },
        alerts: [],
      },
      isLoading: false,
      isError: false,
    } as any);

    renderComponent();
    expect(screen.getByText(/sem dados suficientes para diagnóstico fitossanitário/i)).toBeInTheDocument();
  });

  it("should render all 4 coffee disease/pest alerts with their risk levels and phenology", () => {
    vi.spyOn(usePhytosanitaryAlertsModule, "usePhytosanitaryAlerts").mockReturnValue({
      data: {
        reference_date: "2026-11-17",
        region: "Sul de Minas Gerais (Varginha)",
        gd_acumulado: 845.2,
        dmf_last_24h: 7.0,
        dmf_last_48h: 15.0,
        phenology: { nodes_per_branch: 3.12, leafiness_pct: 98.4 },
        alerts: [
          {
            disease_key: "coffee_rust",
            name: "Ferrugem do Cafeeiro",
            scientific_name: "Hemileia vastatrix",
            risk_level: "high",
            status_label: "Crítico (Muito Favorável)",
            risk_score: 78.5,
            estimated_incidence_pct: 8.4,
            control_threshold_pct: 5.0,
            favorable_conditions: "Temp. média 22.1°C, DMF 7.0h",
            recommendation: "Amostrar terço médio e inferior.",
            references: ["Aparecido (2019)", "Pozza et al. (2021)"],
          },
          {
            disease_key: "phoma",
            name: "Mancha-de-Phoma",
            scientific_name: "Phoma tarda",
            risk_level: "moderate",
            status_label: "Atenção (Favorável)",
            risk_score: 48.0,
            estimated_incidence_pct: 12.1,
            audpc_index: 165.4,
            germ_tube_length_um: 118.2,
            favorable_conditions: "Temp. 18.5°C, DMF 48h de 15.0h",
            recommendation: "Monitorar brotações novas.",
            references: ["Lorenzetti et al. (2015)", "Silva et al. (2025)"],
          },
        ],
      },
      isLoading: false,
      isError: false,
    } as any);

    renderComponent();

    expect(screen.getByText("Ferrugem do Cafeeiro")).toBeInTheDocument();
    expect(screen.getByText("Mancha-de-Phoma")).toBeInTheDocument();
    expect(screen.getByText("Crítico (Muito Favorável)")).toBeInTheDocument();
    expect(screen.getByText("Atenção (Favorável)")).toBeInTheDocument();
    expect(screen.getByText("8.4%")).toBeInTheDocument();
    expect(screen.getByText("3.1 nós/ramo")).toBeInTheDocument();
    expect(screen.getByText("98.4%")).toBeInTheDocument();
  });
});
