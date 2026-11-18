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

export type RiskLevel = "low" | "moderate" | "high";

export interface CoffeePhenology {
  nodes_per_branch: number;
  leafiness_pct: number;
}

export interface PhytosanitaryAlertItem {
  disease_key: string;
  name: string;
  scientific_name: string;
  risk_level: RiskLevel;
  status_label: string;
  risk_score: number;
  estimated_incidence_pct: number;
  control_threshold_pct?: number | null;
  audpc_index?: number | null;
  germ_tube_length_um?: number | null;
  favorable_conditions: string;
  recommendation: string;
  references: string[];
}

export interface PhytosanitaryReport {
  reference_date: string | null;
  region: string;
  gd_acumulado: number;
  dmf_last_24h: number;
  dmf_last_48h: number;
  phenology: CoffeePhenology;
  alerts: PhytosanitaryAlertItem[];
}

