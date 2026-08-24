interface GaugeDialProps {
  value: number | null;
  min: number;
  max: number;
  unit: string;
  color: string;
  label: string;
  trendIndicator?: React.ReactNode;
}

const SIZE = 120;
const STROKE = 5;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
/** Show 270° of arc (¾ turn) so the gauge has a visible gap at the bottom. */
const ARC_FRACTION = 0.75;
const ARC_LENGTH = CIRCUMFERENCE * ARC_FRACTION;

export function GaugeDial({ value, min, max, unit, color, label, trendIndicator }: GaugeDialProps) {
  const clampedValue = value !== null ? Math.max(min, Math.min(max, value)) : min;
  const ratio = (clampedValue - min) / (max - min);
  const progressLength = ARC_LENGTH * ratio;

  /** Rotate so the gap sits at the bottom-center. */
  const rotationDeg = 135;

  return (
    <div className="gauge-dial">
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        aria-label={`${label}: ${value !== null ? `${value} ${unit}` : "sem dados"}`}
      >
        {/* Background track */}
        <circle
          className="gauge-dial__track"
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          strokeDasharray={`${ARC_LENGTH} ${CIRCUMFERENCE}`}
          transform={`rotate(${rotationDeg} ${SIZE / 2} ${SIZE / 2})`}
        />
        {/* Progress arc */}
        <circle
          className="gauge-dial__progress"
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          stroke={color}
          strokeDasharray={`${progressLength} ${CIRCUMFERENCE}`}
          strokeDashoffset={0}
          transform={`rotate(${rotationDeg} ${SIZE / 2} ${SIZE / 2})`}
        />
      </svg>

      <span className="gauge-dial__value" style={{ color }}>
        {value !== null ? `${value.toFixed(1)} ${unit}` : "—"}
        {trendIndicator}
      </span>

      <span className="gauge-dial__label">{label}</span>
    </div>
  );
}
