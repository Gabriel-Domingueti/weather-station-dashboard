import { useQuery } from "@tanstack/react-query";
import { fetchHistory } from "@/infra/api";
import type { DateRange, MetricType } from "@/domain/types";

export function useHistoricalData(range: DateRange, metric?: MetricType, city?: string) {
  return useQuery({
    queryKey: ["readings", "history", range, metric, city],
    queryFn: () => fetchHistory(range, metric, city),
    enabled: Boolean(range.start && range.end),
  });
}
