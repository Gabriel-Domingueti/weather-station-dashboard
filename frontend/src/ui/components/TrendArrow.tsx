interface TrendArrowProps {
  trend: "rising" | "falling" | "stable";
}

export function TrendArrow({ trend }: TrendArrowProps) {
  const getIcon = () => {
    switch (trend) {
      case "rising": return "▲";
      case "falling": return "▼";
      case "stable": return "—";
      default: return "—";
    }
  };

  return (
    <span style={{ color: "var(--color-trend)", marginLeft: "4px", fontSize: "0.8em" }}>
      {getIcon()}
    </span>
  );
}
