import { ALL, type FilterState } from '../lib/filters';

interface Props {
  filters: FilterState;
  departments: string[];
  researchAreas: string[];
  maxEvidence: number;
  onChange: (patch: Partial<FilterState>) => void;
  resultCount: number;
}

export function Toolbar({
  filters,
  departments,
  researchAreas,
  maxEvidence,
  onChange,
  resultCount,
}: Props) {
  return (
    <div className="toolbar" role="search">
      <div className="field field--search">
        <label htmlFor="search">Search institutions</label>
        <input
          id="search"
          className="input"
          type="search"
          placeholder="Name or department…"
          value={filters.search}
          onChange={(e) => onChange({ search: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="department">Department</label>
        <select
          id="department"
          className="select"
          value={filters.department}
          onChange={(e) => onChange({ department: e.target.value })}
        >
          <option value={ALL}>All departments</option>
          {departments.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="research-area">Research area</label>
        <select
          id="research-area"
          className="select"
          value={filters.researchArea}
          onChange={(e) => onChange({ researchArea: e.target.value })}
        >
          <option value={ALL}>All areas</option>
          {researchAreas.map((area) => (
            <option key={area} value={area}>
              {area}
            </option>
          ))}
        </select>
      </div>

      <div className="field evidence-filter">
        <label htmlFor="min-evidence">
          Min. evidence: {filters.minEvidence} {filters.minEvidence === 1 ? 'item' : 'items'}
        </label>
        <input
          id="min-evidence"
          type="range"
          min={0}
          max={Math.max(maxEvidence, 1)}
          value={filters.minEvidence}
          onChange={(e) => onChange({ minEvidence: Number(e.target.value) })}
        />
      </div>

      <div className="toolbar__right">
        <span className="small muted" aria-live="polite">
          {resultCount} {resultCount === 1 ? 'institution' : 'institutions'}
        </span>
        <div className="segmented" role="group" aria-label="Switch between map and list view">
          <button
            type="button"
            aria-pressed={filters.view === 'map'}
            onClick={() => onChange({ view: 'map' })}
          >
            Map
          </button>
          <button
            type="button"
            aria-pressed={filters.view === 'list'}
            onClick={() => onChange({ view: 'list' })}
          >
            List
          </button>
        </div>
      </div>
    </div>
  );
}
