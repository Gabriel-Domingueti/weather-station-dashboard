import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MetricType, WeatherReading } from "@/domain/types";

const METRIC_LABELS: Record<MetricType, string> = {
  temperature: "Temperatura (°C)",
  humidity: "Umidade (%)",
  pressure: "Pressão (hPa)",
};

interface Props {
  data: WeatherReading[];
  metric: MetricType;
}

export function WeatherChart({ data, metric }: Props) {
  const chartData = data.map((reading) => ({
    timestamp: new Date(reading.timestamp).toLocaleDateString("pt-BR"),
    value: reading[metric],
  }));

  return (
    <div className="card">
      <h3>{METRIC_LABELS[metric]}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis domain={["auto", "auto"]} />
          <Tooltip />
          <Line type="monotone" dataKey="value" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
