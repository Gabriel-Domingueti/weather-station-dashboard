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

export interface LatestReadingResponse {
  reading: WeatherReading | null;
  is_stale: boolean;
  minutes_since_reading: number | null;
}

export interface MetricRecord {
  max_value: number | null;
  max_date: string | null;
  min_value: number | null;
  min_date: string | null;
}

export interface MonthlyRecords {
  month: string;
  temperature: MetricRecord;
  humidity: MetricRecord;
  pressure: MetricRecord;
}

export interface TrendInfo {
  temperature: "rising" | "falling" | "stable";
  humidity: "rising" | "falling" | "stable";
  pressure: "rising" | "falling" | "stable";
  pressure_change_hpa: number | null;
  rain_alert: boolean;
}

export interface AgroIndex {
  date: string;
  gd: number | null;
  gd_acumulado: number | null;
  dmf_hours: number | null;
}
