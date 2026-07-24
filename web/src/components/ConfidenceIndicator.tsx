import { confidenceIndex, confidenceLabel } from '../lib/format';
import type { Confidence } from '../types';

interface Props {
  level: Confidence | null;
  showLabel?: boolean;
}

/**
 * Neutral, monochrome confidence indicator — three segments filled to the level.
 * Deliberately not a red/amber/green rating.
 */
export function ConfidenceIndicator({ level, showLabel = true }: Props) {
  const filled = level ? confidenceIndex(level) : 0;
  return (
    <span className="confidence" title={confidenceLabel(level)}>
      <span className="confidence__segments" aria-hidden="true">
        {[1, 2, 3].map((segment) => (
          <span
            key={segment}
            className={`confidence__segment${segment <= filled ? ' confidence__segment--on' : ''}`}
          />
        ))}
      </span>
      {showLabel ? (
        <span>{confidenceLabel(level)}</span>
      ) : (
        <span className="visually-hidden">{confidenceLabel(level)}</span>
      )}
    </span>
  );
}
