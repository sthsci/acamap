import { pluralise } from '../lib/format';

interface Props {
  items: number;
  authors: number;
  withheld?: number;
}

/** Neutral evidence readout: how much material a summary rests on. */
export function EvidenceBadge({ items, authors, withheld = 0 }: Props) {
  return (
    <span className="badge" title="Amount of source material behind this summary">
      <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
        <path d="M4 5h16v2H4zm0 6h16v2H4zm0 6h10v2H4z" />
      </svg>
      <span>
        {pluralise(items, 'item')} · {pluralise(authors, 'author')}
        {withheld > 0 && ` · ${withheld} withheld`}
      </span>
    </span>
  );
}
