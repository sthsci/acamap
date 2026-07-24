import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ConfidenceIndicator } from './ConfidenceIndicator';

describe('ConfidenceIndicator', () => {
  it('fills segments according to the level', () => {
    const { container } = render(<ConfidenceIndicator level="medium" />);
    expect(container.querySelectorAll('.confidence__segment--on')).toHaveLength(2);
    expect(screen.getByText('Medium confidence')).toBeInTheDocument();
  });

  it('fills no segments and labels missing data when null', () => {
    const { container } = render(<ConfidenceIndicator level={null} />);
    expect(container.querySelectorAll('.confidence__segment--on')).toHaveLength(0);
    expect(screen.getAllByText('Not enough data').length).toBeGreaterThan(0);
  });

  it('is not a red/amber/green rating (segments share one class)', () => {
    const { container } = render(<ConfidenceIndicator level="high" />);
    const on = container.querySelectorAll('.confidence__segment--on');
    expect(on).toHaveLength(3);
  });
});
