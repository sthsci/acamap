import { describe, expect, it } from 'vitest';

import { locationCountLabel, locationTypeLabel } from './locations';
import { institution } from '../test/fixtures';

describe('public location labels', () => {
  it('uses Campus only for official campus types', () => {
    expect(locationTypeLabel('university_campus')).toBe('Campus');
    expect(locationTypeLabel('medical_research_campus')).toBe('Campus');
    expect(locationTypeLabel('research_institute')).toBe('Institute');
    expect(locationTypeLabel('research_location')).toBe('Research location');
  });

  it('uses Locations as the institution-wide umbrella', () => {
    expect(locationCountLabel(institution.campuses)).toBe('2 locations');
  });
});
