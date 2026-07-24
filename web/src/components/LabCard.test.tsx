import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { insufficientLab, publishedLab } from '../test/fixtures';
import { LabCard } from './LabCard';

describe('LabCard', () => {
  it('renders a published summary with themes and the perceptions note', () => {
    render(<LabCard lab={publishedLab} />);
    expect(screen.getByText('Adaptive Systems Lab')).toBeInTheDocument();
    expect(screen.getByText(/Supportive supervision/)).toBeInTheDocument();
    expect(screen.getByText(/Workload and hours/)).toBeInTheDocument();
    expect(screen.getByText(/9 items · 5 authors/)).toBeInTheDocument();
    expect(screen.getByText(/User-reported perceptions, not verified facts/i)).toBeInTheDocument();
  });

  it('renders the insufficient-data message and no themes', () => {
    render(<LabCard lab={insufficientLab} />);
    expect(
      screen.getByText('Insufficient public data for a reliable summary.'),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Recurring positive themes/)).not.toBeInTheDocument();
  });
});
