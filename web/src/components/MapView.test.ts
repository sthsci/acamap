import { describe, expect, it } from 'vitest';

import { institution } from '../test/fixtures';
import { buildCampusMarkers, campusMarkerIcon } from '../lib/mapMarkers';

describe('campus map markers', () => {
  it('renders one marker per campus with campus statistics', () => {
    const markers = buildCampusMarkers([institution]);
    expect(markers).toHaveLength(institution.campuses.length);

    const html = String(campusMarkerIcon(markers[0], false).options.html);
    expect(html).toContain('role="img"');
    expect(html).toContain('South Kensington Campus');
    expect(html).toContain('5 source items');
    expect(html).toContain('Location summary available');
  });

  it('keeps nearby campuses individually addressable', () => {
    const closeInstitution = {
      ...institution,
      campuses: institution.campuses.map((campus, index) => ({
        ...campus,
        latitude: 51.5 + index * 0.00001,
        longitude: -0.17,
      })),
    };
    const markers = buildCampusMarkers([closeInstitution]);
    expect(new Set(markers.map((marker) => marker.campus.campus_id)).size).toBe(2);
    expect(new Set(markers.map((marker) => marker.position.join(','))).size).toBe(2);
  });

  it('provides keyboard-oriented marker labels', () => {
    const marker = buildCampusMarkers([institution])[0];
    const html = String(campusMarkerIcon(marker, true).options.html);
    expect(html).toContain('aria-label=');
    expect(html).toContain('represented lab');
  });
});
