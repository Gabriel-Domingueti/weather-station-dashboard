import { useAgroIndices } from "@/application/hooks/useAgroIndices";
import "@/ui/styles/AgroIndicesCard.css";

export function AgroIndicesCard() {
  const { data, isLoading, isError } = useAgroIndices();

  let content;

  if (isLoading) {
    content = <div className="loading">Carregando índices...</div>;
  } else if (isError) {
    content = <div className="error">Erro ao carregar os índices.</div>;
  } else if (!data || data.length === 0) {
    content = <div className="empty">sem dados de índices ainda</div>;
  } else {
    const latest = data[data.length - 1];
    content = (
      <div className="metrics">
        <div className="metric">
          <span className="label">GD Acumulado</span>
          <span className="value">
            {latest.gd_acumulado !== null ? latest.gd_acumulado.toFixed(1) : "--"}
          </span>
        </div>
        <div className="metric">
          <span className="label">DMF Diário</span>
          <span className="value">
            {latest.dmf_hours !== null ? `${latest.dmf_hours.toFixed(1)}h` : "--"}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="agro-indices-card card">
      <h2>Índices Agrometeorológicos</h2>
      {content}
      <div className="provisional-warning">
        <span>⚠️</span>
        <p>
          Parâmetros de cálculo (Temperatura Basal e Limiar de DMF) são provisórios, pendentes de validação científica.
        </p>
      </div>
    </div>
  );
}
