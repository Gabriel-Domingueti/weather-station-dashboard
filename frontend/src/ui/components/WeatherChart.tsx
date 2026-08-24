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
    timestamp: reading.timestamp, // mantém o ISO original; formatação só no tick/tooltip
    value: reading[metric],
  }));

  const lineColor = METRIC_COLORS[metric];
  const tickInterval = Math.max(0, Math.ceil(chartData.length / 7) - 1);

  return (
    <div className="card chart-card">
      <h3>{METRIC_LABELS[metric]}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid stroke="#2A343F" strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            interval={tickInterval}
            tickFormatter={(iso: string) =>
              new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })
            }
            tick={{ fontSize: 11, fill: "#8FA0AF" }}
            angle={-30}
            textAnchor="end"
            height={50}
          />
          <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#8FA0AF" }} />
          <Tooltip
            labelFormatter={(iso: string) => new Date(iso).toLocaleString("pt-BR")}
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