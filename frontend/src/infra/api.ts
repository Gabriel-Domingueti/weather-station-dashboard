import axios from "axios";
import type { DailySummary, DateRange, MetricType, WeatherReading, LatestReadingResponse, MonthlyRecords, TrendInfo, AgroIndex } from "@/domain/types";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient = axios.create({ baseURL });

export async function fetchLatestReading(): Promise<LatestReadingResponse> {
  const { data } = await apiClient.get<LatestReadingResponse>("/readings/latest");
  return data;
}

export async function fetchDailySummary(range?: DateRange): Promise<DailySummary[]> {
  const { data } = await apiClient.get<DailySummary[]>("/readings/daily-summary", {
    params: range,
  });
  return data;
}

export async function fetchHistory(
  range: DateRange,
  metric?: MetricType
): Promise<WeatherReading[]> {
  const { data } = await apiClient.get<WeatherReading[]>("/readings/history", {
    params: { ...range, metric },
  });
  return data;
}

export async function fetchMonthlyRecords(year?: number, month?: number): Promise<MonthlyRecords> {
  const { data } = await apiClient.get<MonthlyRecords>("/readings/monthly-records", {
    params: { year, month },
  });
  return data;
}

export async function fetchTrend(): Promise<TrendInfo> {
  const { data } = await apiClient.get<TrendInfo>("/readings/trend");
  return data;
}

export async function fetchAgroIndices(start?: string, end?: string): Promise<AgroIndex[]> {
  const { data } = await apiClient.get<AgroIndex[]>("/readings/agro-indices", {
    params: { start, end },
  });
  return data;
}
