/** Placeholder for future longitudinal trend visualisations. */
export function TrendPlaceholder() {
  return (
    <div className="trend" role="note">
      <svg
        className="trend__spark"
        width="64"
        height="28"
        viewBox="0 0 64 28"
        aria-hidden="true"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <path d="M1 22 L13 16 L23 19 L34 9 L45 12 L54 5 L63 8" strokeDasharray="3 3" />
      </svg>
      <span>
        Longitudinal trends are planned. The data model already records repeated engagement
        snapshots, so changes over time can be visualised here once enough data accumulates.
      </span>
    </div>
  );
}
