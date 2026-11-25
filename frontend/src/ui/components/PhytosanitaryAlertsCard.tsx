import { useState } from "react";
import { usePhytosanitaryAlerts } from "@/application/hooks/usePhytosanitaryAlerts";
import "@/ui/styles/PhytosanitaryAlertsCard.css";

export const SUL_DE_MINAS_CITIES = [
  { key: "varginha", label: "Varginha" },
  { key: "tres_pontas", label: "Três Pontas" },
  { key: "muzambinho", label: "Muzambinho" },
  { key: "boa_esperanca", label: "Boa Esperança" },
  { key: "carmo_de_minas", label: "Carmo de Minas" },
  { key: "guaxupe", label: "Guaxupé" },
  { key: "alfenas", label: "Alfenas" },
  { key: "nova_resende", label: "Nova Resende" },
  { key: "carmo_do_rio_claro", label: "Carmo do Rio Claro" },
  { key: "santo_antonio_do_amparo", label: "Sto. Antônio do Amparo" },
] as const;

export function PhytosanitaryAlertsCard() {
  const [selectedCity, setSelectedCity] = useState<string>("varginha");
  const { data, isLoading, isError } = usePhytosanitaryAlerts(selectedCity);

  const citySelector = (
    <div className="city-selector" role="group" aria-label="Selecionar cidade do Sul de Minas">
      {SUL_DE_MINAS_CITIES.map((city) => (
        <button
          key={city.key}
          type="button"
          className={`city-selector__btn ${selectedCity === city.key ? "active" : ""}`}
          onClick={() => setSelectedCity(city.key)}
        >
          {city.label}
        </button>
      ))}
    </div>
  );

  if (isLoading) {
    return (
      <section className="phytosanitary-card card">
        <div className="phytosanitary-header">
          <h2>Alertas para a Lavoura de Café</h2>
        </div>
        {citySelector}
        <div className="loading">Verificando condições do clima...</div>
      </section>
    );
  }

  if (isError) {
    return (
      <section className="phytosanitary-card card">
        <div className="phytosanitary-header">
          <h2>Alertas para a Lavoura de Café</h2>
        </div>
        {citySelector}
        <div className="error">Erro ao carregar o diagnóstico fitossanitário.</div>
      </section>
    );
  }

  if (!data || data.alerts.length === 0) {
    return (
      <section className="phytosanitary-card card">
        <div className="phytosanitary-header">
          <h2>Alertas para a Lavoura de Café</h2>
        </div>
        {citySelector}
        <div className="empty">Sem dados suficientes para diagnóstico fitossanitário</div>
      </section>
    );
  }

  return (
    <section className="phytosanitary-card card">
      <div className="phytosanitary-header">
        <h2>Alertas para a Lavoura de Café</h2>
        <span className="phytosanitary-subtitle">{data.region}</span>
      </div>

      {citySelector}

      <div className="alerts-grid">
        {data.alerts.map((alert) => (
          <article
            key={alert.disease_key}
            className={`alert-tile alert-tile--${alert.risk_level}`}
          >
            <div className="alert-tile__top">
              <h3 className="alert-tile__title">{alert.name}</h3>
              <span className={`risk-badge risk-badge--${alert.risk_level}`}>
                {alert.status_label}
              </span>
            </div>

            <p className="alert-tile__recommendation">{alert.recommendation}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
