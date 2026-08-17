import { useQuery } from "@tanstack/react-query";
import { fetchLatestReading } from "@/infra/api";

export function useLatestReading() {
  return useQuery({
    queryKey: ["readings", "latest"],
    queryFn: fetchLatestReading,
    refetchInterval: 60_000, // repuxa a cada 1 min pra sensação de "ao vivo"
  });
}
