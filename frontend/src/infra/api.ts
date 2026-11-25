import axios from "axios";
import type {
  DailySummary,
  DateRange,
  MetricType,
  WeatherReading,
  LatestReadingResponse,
  MonthlyRecords,
  TrendInfo,
  AgroIndex,
  PhytosanitaryReport,
} from "@/domain/types";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient = axios.create({ baseURL });

export async function fetchLatestReading(city?: string): Promise<LatestReadingResponse> {
  const { data } = await apiClient.get<LatestReadingResponse>("/readings/latest", {
    params: city ? { city } : undefined,
  });
  return data;
}

export async function fetchDailySummary(range?: DateRange, city?: string): Promise<DailySummary[]> {
  const { data } = await apiClient.get<DailySummary[]>("/readings/daily-summary", {
    params: { ...range, ...(city ? { city } : {}) },
  });
  return data;
}

export async function fetchHistory(
  range: DateRange,
  metric?: MetricType,
  city?: string
): Promise<WeatherReading[]> {
  const { data } = await apiClient.get<WeatherReading[]>("/readings/history", {
    params: { ...range, metric, ...(city ? { city } : {}) },
  });
  return data;
}

export async function fetchMonthlyRecords(
  year?: number,
  month?: number,
  city?: string
): Promise<MonthlyRecords> {
  const { data } = await apiClient.get<MonthlyRecords>("/readings/monthly-records", {
    params: { year, month, ...(city ? { city } : {}) },
  });
  return data;
}

export async function fetchTrend(city?: string): Promise<TrendInfo> {
  const { data } = await apiClient.get<TrendInfo>("/readings/trend", {
    params: city ? { city } : undefined,
  });
  return data;
}

export async function fetchAgroIndices(start?: string, end?: string, city?: string): Promise<AgroIndex[]> {
  const { data } = await apiClient.get<AgroIndex[]>("/readings/agro-indices", {
    params: { start, end, ...(city ? { city } : {}) },
  });
  return data;
}

export async function fetchPhytosanitaryAlerts(
  city: string = "varginha",
  targetDate?: string
): Promise<PhytosanitaryReport> {
  const { data } = await apiClient.get<PhytosanitaryReport>("/readings/phytosanitary-alerts", {
    params: { city, target_date: targetDate },
  });
  return data;
}
