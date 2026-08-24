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
    <span className="trend-arrow">
      {getIcon()}
    </span>
  );
}
