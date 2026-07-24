import type { CampusLocationType, PublicCampus } from '../types';

export function locationTypeLabel(type: CampusLocationType): string {
  if (type === 'university_campus' || type === 'medical_research_campus') {
    return 'Campus';
  }
  if (type === 'research_institute') {
    return 'Institute';
  }
  return 'Research location';
}

export function locationCountLabel(locations: PublicCampus[]): string {
  return `${locations.length} ${locations.length === 1 ? 'location' : 'locations'}`;
}
