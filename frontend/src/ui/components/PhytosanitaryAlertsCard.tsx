import { usePhytosanitaryAlerts } from "@/application/hooks/usePhytosanitaryAlerts";
import "@/ui/styles/PhytosanitaryAlertsCard.css";

export function PhytosanitaryAlertsCard() {
  const { data, isLoading, isError } = usePhytosanitaryAlerts();

  if (isLoading) {
    return (
      <section className="phytosanitary-card card">
        <h2>Alertas Fitossanitários do Cafeeiro</h2>
        <div className="loading">Calculando modelos agrometeorológicos...</div>
      </section>
    );
  }

  if (isError) {
    return (
      <section className="phytosanitary-card card">
        <h2>Alertas Fitossanitários do Cafeeiro</h2>
        <div className="error">Erro ao carregar o diagnóstico fitossanitário.</div>
      </section>
    );
  }

  if (!data || data.alerts.length === 0) {
    return (
      <section className="phytosanitary-card card">
        <h2>Alertas Fitossanitários do Cafeeiro</h2>
        <div className="empty">Sem dados suficientes para diagnóstico fitossanitário</div>
      </section>
    );
  }

  return (
    <section className="phytosanitary-card card">
      <div className="phytosanitary-header">
        <h2>Alertas Fitossanitários do Cafeeiro</h2>
        <span className="phytosanitary-subtitle">
          {data.region} {data.reference_date ? `• Ref: ${data.reference_date}` : ""}
        </span>
      </div>

      <div className="phenology-bar">
        <div className="phenology-item">
          <span className="phenology-label">Graus-Dia (desde 01/Set)</span>
          <span className="phenology-value">{data.gd_acumulado.toFixed(1)} °C·dia</span>
        </div>
        <div className="phenology-item">
          <span className="phenology-label">Molhamento Foliar (48h)</span>
          <span className="phenology-value">{data.dmf_last_48h.toFixed(1)}h</span>
        </div>
        <div className="phenology-item">
          <span className="phenology-label">Crescimento Fenológico (NN)</span>
          <span className="phenology-value">{data.phenology.nodes_per_branch.toFixed(1)} nós/ramo</span>
        </div>
        <div className="phenology-item">
          <span className="phenology-label">Enfolhamento Estimado (LF)</span>
          <span className="phenology-value">{data.phenology.leafiness_pct.toFixed(1)}%</span>
        </div>
      </div>

      <div className="alerts-grid">
        {data.alerts.map((alert) => (
          <article
            key={alert.disease_key}
            className={`alert-tile alert-tile--${alert.risk_level}`}
          >
            <div className="alert-tile__top">
              <div>
                <h3 className="alert-tile__title">{alert.name}</h3>
                <span className="alert-tile__scientific">{alert.scientific_name}</span>
              </div>
              <span className={`risk-badge risk-badge--${alert.risk_level}`}>
                {alert.status_label}
              </span>
            </div>

            <div className="alert-tile__metrics">
              <div>
                <span className="alert-tile__metric-label">Incidência / Severidade Est.</span>
                <strong>{alert.estimated_incidence_pct.toFixed(1)}%</strong>
              </div>
              <div>
                <span className="alert-tile__metric-label">Índice de Risco</span>
                <strong>{alert.risk_score.toFixed(0)}/100</strong>
              </div>
              {alert.audpc_index !== undefined && alert.audpc_index !== null && (
                <div>
                  <span className="alert-tile__metric-label">AACPD (Phoma)</span>
                  <strong>{alert.audpc_index.toFixed(0)}</strong>
                </div>
              )}
            </div>

            <p className="alert-tile__conditions">{alert.favorable_conditions}</p>
            <p className="alert-tile__recommendation">{alert.recommendation}</p>
            <span className="alert-tile__refs">
              Base: {alert.references.join(" • ")}
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}
