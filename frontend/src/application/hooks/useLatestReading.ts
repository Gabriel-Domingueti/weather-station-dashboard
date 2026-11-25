import { useQuery } from "@tanstack/react-query";
import { fetchLatestReading } from "@/infra/api";

export function useLatestReading(city?: string) {
  return useQuery({
    queryKey: ["readings", "latest", city],
    queryFn: () => fetchLatestReading(city),
    refetchInterval: 60_000,
  });
}
