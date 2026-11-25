import { useQuery } from "@tanstack/react-query";
import { fetchTrend } from "@/infra/api";

export function useTrend(city?: string) {
  return useQuery({
    queryKey: ["readings", "trend", city],
    queryFn: () => fetchTrend(city),
    refetchInterval: 60_000,
  });
}
