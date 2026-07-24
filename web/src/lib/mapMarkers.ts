import L from 'leaflet';

import type { EvidenceStatus, PublicCampus, PublicInstitution } from '../types';

export interface CampusMarker {
  institution: PublicInstitution;
  campus: PublicCampus;
  position: [number, number];
  campusIndex: number;
}

const INSTITUTION_COLOURS = ['#46557a', '#8a4f5f', '#3f6b5a', '#765b36', '#604f82', '#38677a'];

function escapeHtml(value: string): string {
  return value.replace(
    /[&<>"']/g,
    (char) =>
      (
        ({
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#039;',
        }) as Record<string, string>
      )[char],
  );
}

function institutionColour(id: string): string {
  const hash = [...id].reduce((total, char) => total + char.charCodeAt(0), 0);
  return INSTITUTION_COLOURS[hash % INSTITUTION_COLOURS.length];
}

export function evidenceLabel(status: EvidenceStatus): string {
  if (status === 'summary_available') return 'Location summary available';
  if (status === 'below_threshold') return 'Evidence below summary threshold';
  return 'No location-assigned evidence';
}

function countLabel(count: number, singular: string): string {
  return `${count} ${singular}${count === 1 ? '' : 's'}`;
}

function distanceMetres(a: [number, number], b: [number, number]): number {
  const latScale = 111_320;
  const lonScale = 111_320 * Math.cos(((a[0] + b[0]) / 2) * (Math.PI / 180));
  return Math.hypot((a[0] - b[0]) * latScale, (a[1] - b[1]) * lonScale);
}

/**
 * Spread markers closer than 60m into a small deterministic ring. This keeps
 * every location individually visible and keyboard-focusable without hiding
 * markers inside an inaccessible visual-only cluster.
 */
export function buildCampusMarkers(institutions: PublicInstitution[]): CampusMarker[] {
  const markers = institutions.flatMap((institution) =>
    institution.campuses.map((campus, campusIndex) => ({
      institution,
      campus,
      campusIndex,
      position: [campus.latitude, campus.longitude] as [number, number],
    })),
  );

  const groups: CampusMarker[][] = [];
  for (const marker of markers) {
    const group = groups.find((candidate) =>
      candidate.some((other) => distanceMetres(marker.position, other.position) < 60),
    );
    if (group) group.push(marker);
    else groups.push([marker]);
  }

  for (const group of groups) {
    if (group.length < 2) continue;
    const center: [number, number] = [
      group.reduce((sum, marker) => sum + marker.position[0], 0) / group.length,
      group.reduce((sum, marker) => sum + marker.position[1], 0) / group.length,
    ];
    group.forEach((marker, index) => {
      const angle = (2 * Math.PI * index) / group.length;
      const radiusMetres = 32;
      marker.position = [
        center[0] + (Math.sin(angle) * radiusMetres) / 111_320,
        center[1] +
          (Math.cos(angle) * radiusMetres) / (111_320 * Math.cos(center[0] * (Math.PI / 180))),
      ];
    });
  }
  return markers;
}

export function campusMarkerIcon(marker: CampusMarker, selected: boolean): L.DivIcon {
  const { institution, campus, campusIndex } = marker;
  const empty = campus.source_item_count === 0;
  const classes = [
    'map-marker',
    selected ? 'map-marker--active' : '',
    empty ? 'map-marker--empty' : '',
  ]
    .filter(Boolean)
    .join(' ');
  const label = String(campusIndex + 1);
  const aria = `${institution.name}, ${campus.name}. ${countLabel(campus.represented_lab_count, 'represented lab')}, ${countLabel(campus.source_item_count, 'source item')}. ${evidenceLabel(campus.evidence_status)}.`;
  return L.divIcon({
    className: '',
    html: `<div class="${classes}" style="--marker-color:${institutionColour(institution.institution_id)}" role="img" aria-label="${escapeHtml(aria)}"><span>${label}</span></div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });
}
