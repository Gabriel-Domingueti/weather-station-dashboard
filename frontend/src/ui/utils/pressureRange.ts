export interface MetricRecord {
  min_value: number | null;
  min_date: string | null;
  max_value: number | null;
  max_date: string | null;
}

export function resolvePressureRange(monthlyPressure: MetricRecord | undefined): { min: number; max: number } {
  if (!monthlyPressure || monthlyPressure.min_value == null || monthlyPressure.max_value == null) {
    return { min: 980, max: 1040 };
  }

  let min = monthlyPressure.min_value - 5;
  let max = monthlyPressure.max_value + 5;

  const amplitude = max - min;
  if (amplitude < 10) {
    const center = (max + min) / 2;
    min = center - 5;
    max = center + 5;
  }

  return { min, max };
}
