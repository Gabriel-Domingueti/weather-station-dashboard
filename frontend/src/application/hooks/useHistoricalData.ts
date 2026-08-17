import { useQuery } from "@tanstack/react-query";
import { fetchHistory } from "@/infra/api";
import type { DateRange, MetricType } from "@/domain/types";

export function useHistoricalData(range: DateRange, metric?: MetricType) {
  return useQuery({
    queryKey: ["readings", "history", range, metric],
    queryFn: () => fetchHistory(range, metric),
    enabled: Boolean(range.start && range.end),
  });
}
