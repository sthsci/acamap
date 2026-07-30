import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DatasetStatus } from './DatasetStatus';
import type { ExportMeta } from '../types';

const meta: ExportMeta = {
  generated_at: '2026-07-30T10:00:00Z',
  model: 'offline-heuristic',
  prompt_version: '2026-07-01',
  min_items: 5,
  min_authors: 3,
  institution_count: 6,
  published_lab_count: 7,
  withheld_lab_count: 6,
  total_source_items: 67,
  dataset_kind: 'synthetic_demo',
  dataset_note: 'Synthetic demonstration records.',
  disclaimer: 'Unverified perceptions.',
};

describe('DatasetStatus', () => {
  it('labels synthetic summaries explicitly', () => {
    render(<DatasetStatus meta={meta} />);
    expect(screen.getByText('Demonstration dataset')).toBeInTheDocument();
    expect(screen.getByText('Synthetic demonstration records.')).toBeInTheDocument();
    expect(screen.getByText('67')).toBeInTheDocument();
  });

  it('labels a completed lawful import separately', () => {
    render(
      <DatasetStatus
        meta={{
          ...meta,
          dataset_kind: 'lawfully_imported',
          dataset_note: 'Sanitised aggregates from a permitted import.',
        }}
      />,
    );
    expect(screen.getByText('Sanitised public-data aggregates')).toBeInTheDocument();
  });
});
