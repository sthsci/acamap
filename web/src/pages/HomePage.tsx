import { useEffect, useMemo, useState } from 'react';

import { BottomSheet } from '../components/BottomSheet';
import { Disclaimer } from '../components/Disclaimer';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { InstitutionPanel } from '../components/InstitutionPanel';
import { ListView } from '../components/ListView';
import { MapView } from '../components/MapView';
import { RegionSelector } from '../components/RegionSelector';
import { Toolbar } from '../components/Toolbar';
import { useDataset } from '../hooks/useDataset';
import { useMediaQuery } from '../hooks/useMediaQuery';
import {
  collectDepartments,
  collectResearchAreas,
  defaultFilters,
  maxEvidence,
  visibleInstitutions,
  type FilterState,
} from '../lib/filters';
import type { CampusSelection, Region } from '../types';

const PANEL_HEADING = 'institution-panel-heading';

function initialRegion(regions: Region[]): string {
  return regions.find((r) => r.status === 'active')?.id ?? regions[0]?.id ?? 'london';
}

export function HomePage() {
  const state = useDataset();
  const isMobile = useMediaQuery('(max-width: 900px)');

  const [region, setRegion] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>(defaultFilters);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedCampus, setSelectedCampus] = useState<CampusSelection>('all');

  const data = state.status === 'ready' ? state.data : null;
  const activeRegion = region ?? (data ? initialRegion(data.regions) : 'london');

  const regionCenter = useMemo<[number, number]>(() => {
    const found = data?.regions.find((r) => r.id === activeRegion);
    return found ? found.center : [51.5142, -0.1183];
  }, [data, activeRegion]);
  const regionZoom = data?.regions.find((r) => r.id === activeRegion)?.zoom ?? 13;

  const institutions = useMemo(() => data?.institutions ?? [], [data]);
  const departments = useMemo(
    () => collectDepartments(institutions, activeRegion),
    [institutions, activeRegion],
  );
  const researchAreas = useMemo(
    () => collectResearchAreas(institutions, activeRegion),
    [institutions, activeRegion],
  );
  const evidenceMax = useMemo(
    () => maxEvidence(institutions.filter((i) => i.region === activeRegion)),
    [institutions, activeRegion],
  );
  const visible = useMemo(
    () => visibleInstitutions(institutions, activeRegion, filters),
    [institutions, activeRegion, filters],
  );

  const selected = visible.find((i) => i.institution_id === selectedId) ?? null;

  // Clear a selection that is no longer visible (region/filter change).
  useEffect(() => {
    if (selectedId && !visible.some((i) => i.institution_id === selectedId)) {
      setSelectedId(null);
      setSelectedCampus('all');
    }
  }, [visible, selectedId]);

  function patchFilters(patch: Partial<FilterState>) {
    setFilters((prev) => ({ ...prev, ...patch }));
  }

  function selectInstitution(id: string, campus: CampusSelection = 'all') {
    setSelectedId(id);
    setSelectedCampus(campus);
  }

  if (state.status === 'loading') {
    return (
      <div className="container">
        <LoadingState label="Loading Lab Vibes London…" />
      </div>
    );
  }
  if (state.status === 'error') {
    return (
      <div className="container">
        <ErrorState message={state.error} />
      </div>
    );
  }

  const showSidePanel = selected !== null && !isMobile;

  return (
    <div className="container">
      <section style={{ paddingTop: 'var(--space-6)' }}>
        <h1>Research workplace impressions across London</h1>
        <p className="muted" style={{ maxWidth: 680 }}>
          Explore recurring themes people report about labs and research groups at London
          universities and institutes. Each marker is a verified campus or research location; select
          one to read aggregated, anonymised summaries.
        </p>
        <div style={{ margin: 'var(--space-4) 0' }}>
          <RegionSelector
            regions={data!.regions}
            active={activeRegion}
            onChange={(id) => {
              setRegion(id);
              setSelectedId(null);
              setSelectedCampus('all');
            }}
          />
        </div>
      </section>

      <Disclaimer />

      <Toolbar
        filters={filters}
        departments={departments}
        researchAreas={researchAreas}
        maxEvidence={evidenceMax}
        onChange={patchFilters}
        resultCount={visible.length}
      />

      {visible.length === 0 ? (
        <EmptyState title="No institutions match your filters">
          Try clearing the search or lowering the minimum-evidence filter.
        </EmptyState>
      ) : (
        <div className={`workspace${showSidePanel ? ' workspace--split' : ''}`}>
          <div>
            <h2 className="visually-hidden">
              {filters.view === 'map' ? 'Map of locations' : 'List of institutions and locations'}
            </h2>
            {filters.view === 'map' ? (
              <ErrorBoundary
                fallback={
                  <div className="map-shell">
                    <EmptyState title="Map could not be displayed">
                      Switch to list view to browse institutions.
                    </EmptyState>
                  </div>
                }
              >
                <MapView
                  institutions={visible}
                  selectedId={selectedId}
                  selectedCampus={selectedCampus}
                  onSelect={selectInstitution}
                  center={regionCenter}
                  zoom={regionZoom}
                />
              </ErrorBoundary>
            ) : (
              <ListView
                institutions={visible}
                selectedId={selectedId}
                selectedCampus={selectedCampus}
                onSelect={selectInstitution}
              />
            )}
          </div>

          {showSidePanel && selected && (
            <aside className="card panel" aria-label="Institution details">
              <InstitutionPanel
                institution={selected}
                filters={filters}
                campusSelection={selectedCampus}
                onCampusChange={setSelectedCampus}
                headingId={PANEL_HEADING}
                onClose={() => {
                  setSelectedId(null);
                  setSelectedCampus('all');
                }}
              />
            </aside>
          )}
        </div>
      )}

      {isMobile && (
        <BottomSheet
          open={selected !== null}
          onClose={() => {
            setSelectedId(null);
            setSelectedCampus('all');
          }}
          labelledBy={PANEL_HEADING}
        >
          {selected && (
            <InstitutionPanel
              institution={selected}
              filters={filters}
              campusSelection={selectedCampus}
              onCampusChange={setSelectedCampus}
              headingId={PANEL_HEADING}
              onClose={() => {
                setSelectedId(null);
                setSelectedCampus('all');
              }}
            />
          )}
        </BottomSheet>
      )}
    </div>
  );
}
