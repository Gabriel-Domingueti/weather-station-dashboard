import { useQuery } from "@tanstack/react-query";
import { fetchPhytosanitaryAlerts } from "@/infra/api";

export function usePhytosanitaryAlerts(targetDate?: string) {
  return useQuery({
    queryKey: ["phytosanitaryAlerts", targetDate],
    queryFn: () => fetchPhytosanitaryAlerts(targetDate),
    staleTime: 5 * 60 * 1000,
  });
}
