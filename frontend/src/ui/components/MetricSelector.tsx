import type { MetricType } from "@/domain/types";

const OPTIONS: { value: MetricType; label: string }[] = [
  { value: "temperature", label: "Temperatura" },
  { value: "humidity", label: "Umidade" },
  { value: "pressure", label: "Pressão" },
];

interface Props {
  value: MetricType;
  onChange: (metric: MetricType) => void;
}

export function MetricSelector({ value, onChange }: Props) {
  return (
    <div className="metric-selector">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          data-metric={option.value}
          className={option.value === value ? "active" : ""}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
