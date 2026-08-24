import { useQuery } from "@tanstack/react-query";
import { fetchMonthlyRecords } from "@/infra/api";

export function useMonthlyRecords(year?: number, month?: number) {
  return useQuery({
    queryKey: ["readings", "monthly-records", year, month],
    queryFn: () => fetchMonthlyRecords(year, month),
    staleTime: 5 * 60 * 1000,
  });
}
