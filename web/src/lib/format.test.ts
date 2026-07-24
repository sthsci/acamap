import { describe, expect, it } from 'vitest';

import { confidenceIndex, confidenceLabel, formatDateRange, pluralise } from './format';

describe('confidence helpers', () => {
  it('maps levels to indices', () => {
    expect(confidenceIndex('low')).toBe(1);
    expect(confidenceIndex('medium')).toBe(2);
    expect(confidenceIndex('high')).toBe(3);
  });

  it('labels levels and null', () => {
    expect(confidenceLabel('high')).toBe('High confidence');
    expect(confidenceLabel(null)).toBe('Not enough data');
  });
});

describe('formatDateRange', () => {
  it('handles missing dates', () => {
    expect(formatDateRange(null, null)).toBe('No date range');
  });

  it('collapses identical start and end', () => {
    expect(formatDateRange('2025-09-01', '2025-09-01')).not.toContain('–');
  });

  it('formats a range', () => {
    expect(formatDateRange('2025-09-01', '2025-10-01')).toContain('–');
  });
});

describe('pluralise', () => {
  it('handles singular and plural', () => {
    expect(pluralise(1, 'item')).toBe('1 item');
    expect(pluralise(3, 'item')).toBe('3 items');
    expect(pluralise(2, 'author')).toBe('2 authors');
  });
});
