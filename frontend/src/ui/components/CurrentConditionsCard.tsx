import { useLatestReading } from "@/application/hooks/useLatestReading";

export function CurrentConditionsCard() {
  const { data, isLoading, isError } = useLatestReading();

  if (isLoading) return <div className="card">Carregando condições atuais...</div>;
  if (isError || !data) return <div className="card">Sem dados recentes da estação.</div>;

  return (
    <div className="card current-conditions">
      <h2>Condições atuais</h2>
      <div className="metrics-row">
        <Metric label="Temperatura" value={data.temperature} unit="°C" />
        <Metric label="Umidade" value={data.humidity} unit="%" />
        <Metric label="Pressão" value={data.pressure} unit="hPa" />
      </div>
      <p className="timestamp">Última leitura: {new Date(data.timestamp).toLocaleString("pt-BR")}</p>
    </div>
  );
}

function Metric({ label, value, unit }: { label: string; value: number | null; unit: string }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value !== null ? `${value.toFixed(1)} ${unit}` : "--"}</span>
    </div>
  );
}
