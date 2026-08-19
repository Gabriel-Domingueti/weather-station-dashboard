import { useLatestReading } from "@/application/hooks/useLatestReading";
import { GaugeDial } from "@/ui/components/GaugeDial";

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

  if (isLoading) return <div className="card"><p className="status-message">Carregando condições atuais…</p></div>;
  if (isError || !data) return <div className="card"><p className="status-message status-message--error">Sem dados recentes da estação.</p></div>;

  return (
    <section className="gauge-grid">
      {GAUGES.map((g) => (
        <GaugeDial
          key={g.key}
          value={data[g.key]}
          min={g.min}
          max={g.max}
          unit={g.unit}
          color={g.color}
          label={g.label}
        />
      ))}
    </section>
  );
}
