import type { Region } from '../types';

interface Props {
  regions: Region[];
  active: string;
  onChange: (id: string) => void;
}

export function RegionSelector({ regions, active, onChange }: Props) {
  return (
    <div className="region-selector" role="group" aria-label="Select region">
      {regions.map((region) => {
        const isActive = region.id === active;
        const comingSoon = region.status === 'coming_soon';
        return (
          <button
            key={region.id}
            type="button"
            className="region-chip"
            aria-pressed={isActive}
            disabled={comingSoon}
            onClick={() => !comingSoon && onChange(region.id)}
            title={comingSoon ? `${region.name} — coming later` : region.name}
          >
            {region.name}
            {comingSoon && <span className="region-chip__status">Coming later</span>}
          </button>
        );
      })}
    </div>
  );
}
