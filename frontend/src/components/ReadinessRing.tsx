import type { CSSProperties } from "react";

interface ReadinessRingProps {
  value: number;
  label: string;
  size?: "small" | "large";
}


export function ReadinessRing({ value, label, size = "large" }: ReadinessRingProps) {
  const safeValue = Math.max(0, Math.min(value, 100));
  return (
    <div
      className={`readiness-ring readiness-ring-${size}`}
      style={{ "--progress": `${safeValue * 3.6}deg` } as CSSProperties}
      role="img"
      aria-label={`${label}: ${safeValue}%`}
    >
      <div className="readiness-ring-inner">
        <strong>{safeValue}%</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}
