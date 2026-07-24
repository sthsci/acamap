import { useEffect, useMemo } from 'react';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';

import { buildCampusMarkers, campusMarkerIcon, evidenceLabel } from '../lib/mapMarkers';
import { locationTypeLabel } from '../lib/locations';
import type { CampusSelection, PublicInstitution } from '../types';

interface Props {
  institutions: PublicInstitution[];
  selectedId: string | null;
  selectedCampus: CampusSelection;
  onSelect: (institutionId: string, campusId: string) => void;
  center: [number, number];
  zoom: number;
}

const prefersDark =
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-color-scheme: dark)').matches === true;

const TILE_URL = prefersDark
  ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
  : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

const ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

function Recenter({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    try {
      map.setView(center, zoom);
    } catch {
      /* The next render recentres if StrictMode is tearing down this map. */
    }
  }, [map, center, zoom]);
  return null;
}

export function MapView({
  institutions,
  selectedId,
  selectedCampus,
  onSelect,
  center,
  zoom,
}: Props) {
  const markers = useMemo(
    () =>
      buildCampusMarkers(institutions).map((marker) => ({
        ...marker,
        icon: campusMarkerIcon(
          marker,
          marker.institution.institution_id === selectedId &&
            marker.campus.campus_id === selectedCampus,
        ),
      })),
    [institutions, selectedId, selectedCampus],
  );

  return (
    <div className="map-shell">
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={false}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer url={TILE_URL} attribution={ATTRIBUTION} />
        <Recenter center={center} zoom={zoom} />
        {markers.map(({ institution, campus, position, icon }) => {
          const title = `${institution.name} — ${campus.name}`;
          return (
            <Marker
              key={campus.campus_id}
              position={position}
              icon={icon}
              title={title}
              alt={title}
              keyboard
              eventHandlers={{
                click: () => onSelect(institution.institution_id, campus.campus_id),
                popupopen: () => onSelect(institution.institution_id, campus.campus_id),
                keypress: (event) => {
                  const keyboardEvent = event.originalEvent as KeyboardEvent;
                  if (keyboardEvent.key === 'Enter' || keyboardEvent.key === ' ') {
                    onSelect(institution.institution_id, campus.campus_id);
                  }
                },
              }}
            >
              <Popup>
                <strong>{institution.name}</strong>
                <br />
                {campus.name}
                <br />
                <em>{locationTypeLabel(campus.location_type)}</em>
                <br />
                {campus.represented_lab_count} represented{' '}
                {campus.represented_lab_count === 1 ? 'lab' : 'labs'} · {campus.source_item_count}{' '}
                source {campus.source_item_count === 1 ? 'item' : 'items'}
                <br />
                <span>{evidenceLabel(campus.evidence_status)}</span>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
