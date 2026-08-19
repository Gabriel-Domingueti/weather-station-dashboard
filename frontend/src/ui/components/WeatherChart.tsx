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

const METRIC_COLORS: Record<MetricType, string> = {
  temperature: "#E8983D",
  humidity: "#3FB8C4",
  pressure: "#7C7FE0",
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

  const lineColor = METRIC_COLORS[metric];

  return (
    <div className="card chart-card">
      <h3>{METRIC_LABELS[metric]}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid stroke="#2A343F" strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{
              background: "#1B232C",
              border: "1px solid #2A343F",
              borderRadius: 4,
              fontFamily: '"IBM Plex Mono", monospace',
              fontSize: "0.8rem",
            }}
            labelStyle={{ color: "#8FA0AF" }}
            itemStyle={{ color: lineColor }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
