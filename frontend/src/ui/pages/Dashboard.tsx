import { useState } from "react";
import { CurrentConditionsCard } from "@/ui/components/CurrentConditionsCard";
import { DateRangeFilter } from "@/ui/components/DateRangeFilter";
import { MetricSelector } from "@/ui/components/MetricSelector";
import { WeatherChart } from "@/ui/components/WeatherChart";
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

  const { data, isLoading, isError } = useHistoricalData(range, metric);

  return (
    <main className="dashboard">
      <header>
        <h1>Estação Meteorológica</h1>
      </header>

      <CurrentConditionsCard />

      <section className="filters">
        <DateRangeFilter value={range} onChange={setRange} />
        <MetricSelector value={metric} onChange={setMetric} />
      </section>

      {isLoading && <p>Carregando histórico...</p>}
      {isError && <p>Não foi possível carregar o histórico.</p>}
      {data && <WeatherChart data={data} metric={metric} />}
    </main>
  );
}
