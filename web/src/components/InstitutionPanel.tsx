import { formatDate, formatDateRange } from '../lib/format';
import type { FilterState } from '../lib/filters';
import { filterLabs } from '../lib/filters';
import type { CampusSelection, PublicInstitution } from '../types';
import { locationTypeLabel } from '../lib/locations';
import { ConfidenceIndicator } from './ConfidenceIndicator';
import { LabCard } from './LabCard';
import { TrendPlaceholder } from './TrendPlaceholder';

interface Props {
  institution: PublicInstitution;
  filters: FilterState;
  campusSelection?: CampusSelection;
  onCampusChange?: (campus: CampusSelection) => void;
  onClose?: () => void;
  headingId?: string;
}

export function InstitutionPanel({
  institution,
  filters,
  campusSelection = 'all',
  onCampusChange,
  onClose,
  headingId,
}: Props) {
  const campus =
    campusSelection === 'all' || campusSelection === 'unspecified'
      ? null
      : (institution.campuses.find((item) => item.campus_id === campusSelection) ?? null);
  const labs = filterLabs(institution, filters, campusSelection);
  const publishedLabs = labs.filter((lab) => lab.has_summary);
  const unspecified = institution.campus_unspecified;
  const isUnspecified = campusSelection === 'unspecified';
  const representedLabs =
    campusSelection === 'all'
      ? institution.represented_lab_count
      : isUnspecified
        ? labs.length
        : (campus?.represented_lab_count ?? 0);
  const sourceItems =
    campusSelection === 'all'
      ? institution.source_item_count
      : isUnspecified
        ? unspecified.source_item_count
        : (campus?.source_item_count ?? 0);
  const authors =
    campusSelection === 'all'
      ? institution.unique_author_count
      : isUnspecified
        ? unspecified.unique_author_count
        : (campus?.unique_author_count ?? 0);
  const dateStart =
    campusSelection === 'all'
      ? institution.date_range_start
      : isUnspecified
        ? unspecified.date_range_start
        : (campus?.provenance?.date_range_start ?? null);
  const dateEnd =
    campusSelection === 'all'
      ? institution.date_range_end
      : isUnspecified
        ? unspecified.date_range_end
        : (campus?.provenance?.date_range_end ?? null);
  const confidence =
    campusSelection === 'all' ? institution.confidence : (campus?.confidence ?? null);

  return (
    <div>
      <div className="panel__header">
        <div>
          <div className="panel__eyebrow">
            {campusSelection === 'all'
              ? 'Institution · All locations'
              : isUnspecified
                ? 'Institution · Location unspecified'
                : `Institution · ${campus?.short_name ?? 'Location'}`}
          </div>
          <h2 className="panel__title" id={headingId}>
            {institution.name}
          </h2>
          {institution.website && (
            <a className="small" href={institution.website} target="_blank" rel="noreferrer">
              {institution.website.replace(/^https?:\/\//, '')}
            </a>
          )}
        </div>
        {onClose && (
          <button type="button" className="btn btn--ghost" onClick={onClose} aria-label="Close">
            ✕
          </button>
        )}
      </div>

      <div className="field campus-select">
        <label htmlFor={`${institution.institution_id}-campus`}>Location</label>
        <select
          id={`${institution.institution_id}-campus`}
          className="select"
          value={campusSelection}
          onChange={(event) => onCampusChange?.(event.target.value as CampusSelection)}
        >
          <option value="all">All locations</option>
          {institution.campuses.map((item) => (
            <option value={item.campus_id} key={item.campus_id}>
              {item.name}
            </option>
          ))}
          {unspecified.source_item_count > 0 && (
            <option value="unspecified">Location unspecified</option>
          )}
        </select>
      </div>

      {campus && (
        <p className="small muted campus-address">
          {locationTypeLabel(campus.location_type)} · {campus.address}
        </p>
      )}
      {isUnspecified && (
        <p className="small muted campus-address">
          These items could not be safely assigned to a physical location.
        </p>
      )}

      <div className="chip-row">
        <ConfidenceIndicator level={confidence} />
        {institution.last_updated && campusSelection === 'all' && (
          <span className="badge">Updated {formatDate(institution.last_updated)}</span>
        )}
      </div>

      <div className="panel__stats">
        <div className="stat">
          <div className="stat__value">{representedLabs}</div>
          <div className="stat__label">Represented labs</div>
        </div>
        <div className="stat">
          <div className="stat__value">{sourceItems}</div>
          <div className="stat__label">Source items</div>
        </div>
        <div className="stat">
          <div className="stat__value">{authors}</div>
          <div className="stat__label">Distinct authors</div>
        </div>
        <div className="stat">
          <div className="stat__value stat__value--date">{formatDateRange(dateStart, dateEnd)}</div>
          <div className="stat__label">Data date range</div>
        </div>
      </div>

      {campus?.summary && (
        <>
          <div className="section-label">Location summary</div>
          <p>{campus.summary.overview}</p>
          <p className="small muted">
            Generated only from location-assigned items meeting the same 5-item, 3-author threshold.
          </p>
        </>
      )}

      {campusSelection === 'all' && institution.overall_themes.length > 0 && (
        <>
          <div className="section-label">Overall recurring themes</div>
          <div className="chip-row">
            {institution.overall_themes.map((theme) => (
              <span className="chip chip--accent" key={theme}>
                {theme}
              </span>
            ))}
          </div>
        </>
      )}

      <div className="section-label">
        Labs {labs.length > 0 && <span className="muted">({labs.length})</span>}
      </div>
      {labs.length === 0 ? (
        <p className="small muted">
          No labs have evidence for this location and the active filters.
        </p>
      ) : (
        labs.map((lab) => <LabCard key={lab.lab_id} lab={lab} campusSelection={campusSelection} />)
      )}

      {publishedLabs.length > 0 && (
        <>
          <div className="section-label">Longitudinal trends</div>
          <TrendPlaceholder />
        </>
      )}
    </div>
  );
}
