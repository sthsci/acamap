import type { CampusSelection, PublicCampusEvidence, PublicInstitution, PublicLab } from '../types';

export interface FilterState {
  search: string;
  department: string;
  researchArea: string;
  minEvidence: number;
  view: 'map' | 'list';
}

export const ALL = 'all';

export const defaultFilters: FilterState = {
  search: '',
  department: ALL,
  researchArea: ALL,
  minEvidence: 0,
  view: 'map',
};

function labMatches(lab: PublicLab, filters: FilterState): boolean {
  if (filters.department !== ALL && lab.department !== filters.department) return false;
  if (filters.researchArea !== ALL && !lab.research_areas.includes(filters.researchArea)) {
    return false;
  }
  const items = lab.provenance?.source_item_count ?? 0;
  if (items < filters.minEvidence) return false;
  return true;
}

/** Labs of an institution that pass the department / research-area / evidence filters. */
export function evidenceForCampus(
  lab: PublicLab,
  campus: CampusSelection,
): PublicCampusEvidence | null {
  if (campus === 'all') return null;
  return (
    lab.campus_evidence.find((item) =>
      campus === 'unspecified' ? item.campus_id === null : item.campus_id === campus,
    ) ?? null
  );
}

export function filterLabs(
  institution: PublicInstitution,
  filters: FilterState,
  campus: CampusSelection = 'all',
): PublicLab[] {
  return institution.labs
    .filter((lab) => labMatches(lab, filters))
    .filter((lab) => campus === 'all' || evidenceForCampus(lab, campus) !== null);
}

function matchesSearch(institution: PublicInstitution, search: string): boolean {
  const q = search.trim().toLowerCase();
  if (!q) return true;
  return (
    institution.name.toLowerCase().includes(q) ||
    institution.short_name.toLowerCase().includes(q) ||
    institution.campuses.some((campus) => campus.name.toLowerCase().includes(q)) ||
    institution.departments.some((d) => d.toLowerCase().includes(q))
  );
}

/** Institutions in the active region that match search and retain ≥1 lab after filtering. */
export function visibleInstitutions(
  institutions: PublicInstitution[],
  region: string,
  filters: FilterState,
): PublicInstitution[] {
  return institutions
    .filter((institution) => institution.region === region)
    .filter((institution) => matchesSearch(institution, filters.search))
    .filter((institution) => {
      const filtersActive =
        filters.department !== ALL || filters.researchArea !== ALL || filters.minEvidence > 0;
      return filtersActive ? filterLabs(institution, filters).length > 0 : true;
    });
}

export function collectDepartments(institutions: PublicInstitution[], region: string): string[] {
  const set = new Set<string>();
  for (const institution of institutions) {
    if (institution.region !== region) continue;
    institution.departments.forEach((d) => set.add(d));
    institution.labs.forEach((lab) => set.add(lab.department));
  }
  return [...set].sort((a, b) => a.localeCompare(b));
}

export function collectResearchAreas(institutions: PublicInstitution[], region: string): string[] {
  const set = new Set<string>();
  for (const institution of institutions) {
    if (institution.region !== region) continue;
    institution.labs.forEach((lab) => lab.research_areas.forEach((area) => set.add(area)));
  }
  return [...set].sort((a, b) => a.localeCompare(b));
}

export function maxEvidence(institutions: PublicInstitution[]): number {
  let max = 0;
  for (const institution of institutions) {
    for (const lab of institution.labs) {
      max = Math.max(max, lab.provenance?.source_item_count ?? 0);
    }
  }
  return max;
}
