import { useState } from "react";
import { CurrentConditionsCard } from "@/ui/components/CurrentConditionsCard";
import { DateRangeFilter } from "@/ui/components/DateRangeFilter";
import { MetricSelector } from "@/ui/components/MetricSelector";
import { WeatherChart } from "@/ui/components/WeatherChart";
import { useLatestReading } from "@/application/hooks/useLatestReading";
import { useHistoricalData } from "@/application/hooks/useHistoricalData";
import type { DateRange, MetricType } from "@/domain/types";

function last7Days(): DateRange {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 7);
  return { start: toISODate(start), end: toISODate(end) };
}

function toISODate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function Dashboard() {
  const [range, setRange] = useState<DateRange>(last7Days());
  const [metric, setMetric] = useState<MetricType>("temperature");

  const { data: latestData } = useLatestReading();
  const { data, isLoading, isError } = useHistoricalData(range, metric);

  const lastUpdated = latestData
    ? new Date(latestData.timestamp).toLocaleString("pt-BR")
    : null;

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <h1>Estação Meteorológica</h1>
        {lastUpdated && (
          <span className="header-timestamp">Atualizado: {lastUpdated}</span>
        )}
      </header>

      <CurrentConditionsCard />

      <section className="filters">
        <DateRangeFilter value={range} onChange={setRange} />
        <MetricSelector value={metric} onChange={setMetric} />
      </section>

      {isLoading && <p className="status-message">Carregando histórico…</p>}
      {isError && <p className="status-message status-message--error">Não foi possível carregar o histórico.</p>}
      {data && <WeatherChart data={data} metric={metric} />}
    </main>
  );
}
