import { useLatestReading } from "@/application/hooks/useLatestReading";
import { useTrend } from "@/application/hooks/useTrend";
import { useMonthlyRecords } from "@/application/hooks/useMonthlyRecords";
import { GaugeDial } from "@/ui/components/GaugeDial";
import { TrendArrow } from "@/ui/components/TrendArrow";
import { resolvePressureRange } from "@/ui/utils/pressureRange";

interface GaugeConfig {
  key: "temperature" | "humidity" | "pressure";
  label: string;
  unit: string;
  min: number;
  max: number;
  color: string;
}

const GAUGES: GaugeConfig[] = [
  {
    key: "temperature",
    label: "temperatura",
    unit: "°C",
    min: 0,
    max: 40,
    color: "var(--color-temperature)",
  },
  {
    key: "humidity",
    label: "umidade",
    unit: "%",
    min: 0,
    max: 100,
    color: "var(--color-humidity)",
  },
  {
    key: "pressure",
    label: "pressão",
    unit: "hPa",
    min: 980,
    max: 1040,
    color: "var(--color-pressure)",
  },
];

export function CurrentConditionsCard() {
  const { data, isLoading, isError } = useLatestReading();
  const { data: trendData } = useTrend();
  const { data: monthlyData } = useMonthlyRecords();

  if (isLoading) return <div className="card"><p className="status-message">Carregando condições atuais…</p></div>;
  if (isError || !data) return <div className="card"><p className="status-message status-message--error">Sem dados recentes da estação.</p></div>;

  return (
    <div>
      {data.is_stale && (
        <div className="stale-badge">
          {data.minutes_since_reading != null
            ? `Última leitura há ${Math.round(data.minutes_since_reading)} min`
            : "Sem dados recentes"}
        </div>
      )}
      {trendData?.rain_alert && (
        <div className="rain-alert-badge">
          💧 Pressão em queda — possível chuva
        </div>
      )}
      <section className="gauge-grid">
      {GAUGES.map((g) => {
        let min = g.min;
        let max = g.max;
        if (g.key === "pressure") {
          const pressureRange = resolvePressureRange(monthlyData?.pressure);
          min = pressureRange.min;
          max = pressureRange.max;
        }

        return (
          <GaugeDial
            key={g.key}
            value={data.reading?.[g.key] ?? null}
            min={min}
            max={max}
            unit={g.unit}
            color={g.color}
            label={g.label}
            trendIndicator={trendData ? <TrendArrow trend={trendData[g.key]} /> : undefined}
          />
        );
      })}
      </section>
    </div>
  );
}
