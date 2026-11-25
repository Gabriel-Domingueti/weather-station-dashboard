import { useQuery } from "@tanstack/react-query";
import { fetchMonthlyRecords } from "@/infra/api";

export function useMonthlyRecords(year?: number, month?: number, city?: string) {
  return useQuery({
    queryKey: ["readings", "monthly-records", year, month, city],
    queryFn: () => fetchMonthlyRecords(year, month, city),
    staleTime: 5 * 60 * 1000,
  });
}
