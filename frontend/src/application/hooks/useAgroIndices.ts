import { useQuery } from "@tanstack/react-query";
import { fetchAgroIndices } from "@/infra/api";

export function useAgroIndices(start?: string, end?: string, city?: string) {
  return useQuery({
    queryKey: ["agroIndices", start, end, city],
    queryFn: () => fetchAgroIndices(start, end, city),
    staleTime: 5 * 60 * 1000,
  });
}
