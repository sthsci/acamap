import { describe, expect, it } from 'vitest';

import { institution } from '../test/fixtures';
import type { PublicInstitution } from '../types';
import {
  collectDepartments,
  collectResearchAreas,
  defaultFilters,
  filterLabs,
  maxEvidence,
  visibleInstitutions,
} from './filters';

const oxford: PublicInstitution = {
  ...institution,
  institution_id: 'oxford-x',
  name: 'Oxford Example',
  region: 'oxford',
};

describe('filterLabs', () => {
  it('returns all labs with default filters', () => {
    expect(filterLabs(institution, defaultFilters)).toHaveLength(2);
  });

  it('filters by department', () => {
    const labs = filterLabs(institution, { ...defaultFilters, department: 'Computing' });
    expect(labs.map((l) => l.lab_name)).toEqual(['Adaptive Systems Lab']);
  });

  it('filters by research area', () => {
    const labs = filterLabs(institution, { ...defaultFilters, researchArea: 'Robotics' });
    expect(labs).toHaveLength(1);
  });

  it('filters by minimum evidence', () => {
    const labs = filterLabs(institution, { ...defaultFilters, minEvidence: 5 });
    expect(labs.map((l) => l.lab_name)).toEqual(['Adaptive Systems Lab']);
  });

  it('filters labs by assigned campus without using catalogue membership alone', () => {
    expect(
      filterLabs(institution, defaultFilters, 'imperial-white-city').map((lab) => lab.lab_name),
    ).toEqual(['Adaptive Systems Lab']);
    expect(
      filterLabs(institution, defaultFilters, 'unspecified').map((lab) => lab.lab_name),
    ).toEqual(['Adaptive Systems Lab']);
  });
});

describe('visibleInstitutions', () => {
  const all = [institution, oxford];

  it('scopes to the active region', () => {
    expect(visibleInstitutions(all, 'london', defaultFilters).map((i) => i.institution_id)).toEqual(
      ['imperial'],
    );
    expect(visibleInstitutions(all, 'oxford', defaultFilters)).toHaveLength(1);
  });

  it('matches search on name and department', () => {
    expect(
      visibleInstitutions(all, 'london', { ...defaultFilters, search: 'imperial' }),
    ).toHaveLength(1);
    expect(
      visibleInstitutions(all, 'london', { ...defaultFilters, search: 'nowhere' }),
    ).toHaveLength(0);
    expect(
      visibleInstitutions(all, 'london', { ...defaultFilters, search: 'computing' }),
    ).toHaveLength(1);
  });

  it('hides institutions with no labs left after filtering', () => {
    const filtered = visibleInstitutions(all, 'london', {
      ...defaultFilters,
      researchArea: 'Nonexistent Area',
    });
    expect(filtered).toHaveLength(0);
  });
});

describe('collectors', () => {
  it('collects departments for a region', () => {
    expect(collectDepartments([institution], 'london')).toContain('Computing');
    expect(collectDepartments([institution], 'london')).toContain('Bioengineering');
  });

  it('collects research areas for a region', () => {
    expect(collectResearchAreas([institution], 'london')).toContain('Machine Learning');
  });

  it('computes max evidence', () => {
    expect(maxEvidence([institution])).toBe(9);
  });
});
