import { useQuery } from "@tanstack/react-query";
import { fetchAgroIndices } from "@/infra/api";

export function useAgroIndices(start?: string, end?: string) {
  return useQuery({
    queryKey: ["agroIndices", start, end],
    queryFn: () => fetchAgroIndices(start, end),
    staleTime: 5 * 60 * 1000,
  });
}
