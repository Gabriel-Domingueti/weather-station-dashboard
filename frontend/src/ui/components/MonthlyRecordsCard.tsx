import { useMonthlyRecords } from "@/application/hooks/useMonthlyRecords";
import type { MetricRecord } from "@/domain/types";

export function MonthlyRecordsCard() {
  const { data, isLoading, isError } = useMonthlyRecords();

  if (isLoading) return <div className="card"><p className="status-message">Carregando recordes do mês…</p></div>;
  if (isError || !data) return <div className="card"><p className="status-message status-message--error">Sem recordes disponíveis.</p></div>;

  const formatDate = (dateStr: string) => {
    const [year, month, day] = dateStr.split("-");
    return `${day}/${month}/${year}`;
  };

  const renderMetric = (label: string, record: MetricRecord, unit: string) => {
    if (record.max_value == null && record.min_value == null) {
      return (
        <div className="monthly-record">
          <strong>{label}:</strong> sem dados ainda
        </div>
      );
    }

    return (
      <div className="monthly-record">
        <strong>{label}:</strong>
        <ul className="monthly-record-list">
          {record.max_value != null && record.max_date != null && (
            <li>Máx: {record.max_value}{unit} em {formatDate(record.max_date)}</li>
          )}
          {record.min_value != null && record.min_date != null && (
            <li>Mín: {record.min_value}{unit} em {formatDate(record.min_date)}</li>
          )}
        </ul>
      </div>
    );
  };

  return (
    <div className="card monthly-records-card">
      <h3 className="monthly-records-header">Recordes do Mês ({data.month})</h3>
      <div className="monthly-records-body">
        {renderMetric("Temperatura", data.temperature, "°C")}
        {renderMetric("Umidade", data.humidity, "%")}
        {renderMetric("Pressão", data.pressure, "hPa")}
      </div>
    </div>
  );
}
