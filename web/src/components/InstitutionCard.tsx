import { pluralise } from '../lib/format';
import { locationCountLabel, locationTypeLabel } from '../lib/locations';
import type { CampusSelection, PublicInstitution, PublicLab } from '../types';
import { ConfidenceIndicator } from './ConfidenceIndicator';

interface Props {
  institution: PublicInstitution;
  selected: boolean;
  selectedCampus: CampusSelection;
  onSelect: (campus: CampusSelection) => void;
}

function labsByDepartment(labs: PublicLab[]): Map<string, PublicLab[]> {
  const grouped = new Map<string, PublicLab[]>();
  for (const lab of labs) {
    grouped.set(lab.department, [...(grouped.get(lab.department) ?? []), lab]);
  }
  return grouped;
}

export function InstitutionCard({ institution, selected, selectedCampus, onSelect }: Props) {
  return (
    <article className={`card institution-card${selected ? ' institution-card--selected' : ''}`}>
      <button
        type="button"
        className="institution-card__select"
        aria-current={selected && selectedCampus === 'all'}
        onClick={() => onSelect('all')}
      >
        <span className="institution-card__head">
          <span className="institution-card__name">{institution.name}</span>
          <ConfidenceIndicator level={institution.confidence} showLabel={false} />
        </span>
        <span className="institution-card__stats">
          <span>{locationCountLabel(institution.campuses)}</span>
          <span>{pluralise(institution.represented_lab_count, 'represented lab')}</span>
          <span>{pluralise(institution.source_item_count, 'item')}</span>
        </span>
        <span className="campus-name-list">
          {institution.campuses.map((campus) => campus.short_name).join(' · ')}
        </span>
      </button>

      <details className="campus-hierarchy">
        <summary>Location, department and lab details</summary>
        {institution.campuses.map((campus) => {
          const campusLabs = institution.labs.filter((lab) =>
            lab.campus_ids.includes(campus.campus_id),
          );
          const departments = labsByDepartment(campusLabs);
          return (
            <section className="campus-branch" key={campus.campus_id}>
              <button
                type="button"
                className="campus-branch__select"
                aria-current={selected && selectedCampus === campus.campus_id}
                onClick={() => onSelect(campus.campus_id)}
              >
                {campus.name} · {locationTypeLabel(campus.location_type)}
                <span>{pluralise(campus.source_item_count, 'item')}</span>
              </button>
              {[...departments.entries()].map(([department, labs]) => (
                <div className="department-branch" key={department}>
                  <div className="department-branch__name">{department}</div>
                  <ul>
                    {labs.map((lab) => (
                      <li key={lab.lab_id}>{lab.lab_name}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </section>
          );
        })}
        {institution.campus_unspecified.source_item_count > 0 && (
          <section className="campus-branch">
            <button
              type="button"
              className="campus-branch__select"
              aria-current={selected && selectedCampus === 'unspecified'}
              onClick={() => onSelect('unspecified')}
            >
              Location unspecified
              <span>{pluralise(institution.campus_unspecified.source_item_count, 'item')}</span>
            </button>
          </section>
        )}
      </details>
    </article>
  );
}
