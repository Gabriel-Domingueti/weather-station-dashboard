import { useQuery } from "@tanstack/react-query";
import { fetchTrend } from "@/infra/api";

export function useTrend() {
  return useQuery({
    queryKey: ["readings", "trend"],
    queryFn: fetchTrend,
    refetchInterval: 60_000,
  });
}
