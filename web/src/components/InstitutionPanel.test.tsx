import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { defaultFilters } from '../lib/filters';
import { institution } from '../test/fixtures';
import { InstitutionPanel } from './InstitutionPanel';

describe('InstitutionPanel', () => {
  it('shows institution stats and both lab states', () => {
    render(<InstitutionPanel institution={institution} filters={defaultFilters} />);

    expect(screen.getByText('Imperial College London')).toBeInTheDocument();
    expect(screen.getByText('Represented labs')).toBeInTheDocument();
    expect(screen.getByText('Source items')).toBeInTheDocument();
    expect(screen.getByText('Distinct authors')).toBeInTheDocument();
    expect(screen.getByLabelText('Location')).toHaveValue('all');

    // published lab + insufficient lab both appear
    expect(screen.getByText('Adaptive Systems Lab')).toBeInTheDocument();
    expect(
      screen.getByText('Insufficient public data for a reliable summary.'),
    ).toBeInTheDocument();

    // overall themes surfaced as chips
    expect(screen.getAllByText('Supportive supervision').length).toBeGreaterThan(0);
  });

  it('respects an active department filter', () => {
    render(
      <InstitutionPanel
        institution={institution}
        filters={{ ...defaultFilters, department: 'Computing' }}
      />,
    );
    expect(screen.getByText('Adaptive Systems Lab')).toBeInTheDocument();
    expect(screen.queryByText('Neurotechnology Lab')).not.toBeInTheDocument();
  });

  it('filters to location evidence and exposes Location unspecified', () => {
    render(
      <InstitutionPanel
        institution={institution}
        filters={defaultFilters}
        campusSelection="unspecified"
      />,
    );
    expect(screen.getByText(/could not be safely assigned/i)).toBeInTheDocument();
    expect(screen.getByText('Adaptive Systems Lab')).toBeInTheDocument();
    expect(screen.queryByText('Neurotechnology Lab')).not.toBeInTheDocument();
  });
});
