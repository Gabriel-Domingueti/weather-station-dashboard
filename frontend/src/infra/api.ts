import axios from "axios";
import type { DailySummary, DateRange, MetricType, WeatherReading } from "@/domain/types";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient = axios.create({ baseURL });

export async function fetchLatestReading(): Promise<WeatherReading | null> {
  const { data } = await apiClient.get<WeatherReading | null>("/readings/latest");
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
