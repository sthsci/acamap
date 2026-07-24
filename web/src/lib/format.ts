import type { Confidence } from '../types';

const CONFIDENCE_INDEX: Record<Confidence, number> = { low: 1, medium: 2, high: 3 };

export function confidenceIndex(level: Confidence): number {
  return CONFIDENCE_INDEX[level];
}

export function confidenceLabel(level: Confidence | null): string {
  if (!level) return 'Not enough data';
  return `${level.charAt(0).toUpperCase()}${level.slice(1)} confidence`;
}

const dateFormatter = new Intl.DateTimeFormat('en-GB', {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
});

export function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return dateFormatter.format(date);
}

export function formatDateRange(start: string | null, end: string | null): string {
  if (!start && !end) return 'No date range';
  if (start && end && start === end) return formatDate(start);
  return `${formatDate(start)} – ${formatDate(end)}`;
}

export function pluralise(count: number, singular: string, plural?: string): string {
  const word = count === 1 ? singular : (plural ?? `${singular}s`);
  return `${count} ${word}`;
}
