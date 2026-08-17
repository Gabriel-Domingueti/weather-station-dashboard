export type MetricType = "temperature" | "humidity" | "pressure";

export interface WeatherReading {
  timestamp: string;
  temperature: number | null;
  humidity: number | null;
  pressure: number | null;
}

export interface DailySummary {
  date: string;
  temperature_avg: number | null;
  temperature_min: number | null;
  temperature_max: number | null;
  humidity_avg: number | null;
  humidity_min: number | null;
  humidity_max: number | null;
  pressure_avg: number | null;
  pressure_min: number | null;
  pressure_max: number | null;
}

export interface DateRange {
  start: string; // YYYY-MM-DD
  end: string;
}
