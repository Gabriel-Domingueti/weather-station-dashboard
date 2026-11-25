import { useQuery } from "@tanstack/react-query";
import { fetchPhytosanitaryAlerts } from "@/infra/api";

export function usePhytosanitaryAlerts(city: string = "varginha", targetDate?: string) {
  return useQuery({
    queryKey: ["phytosanitaryAlerts", city, targetDate],
    queryFn: () => fetchPhytosanitaryAlerts(city, targetDate),
    staleTime: 5 * 60 * 1000,
  });
}
