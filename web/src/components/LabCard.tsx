import { formatDateRange } from '../lib/format';
import { evidenceForCampus } from '../lib/filters';
import type { CampusSelection, PublicLab } from '../types';
import { ConfidenceIndicator } from './ConfidenceIndicator';
import { PerceptionsNote } from './Disclaimer';
import { EvidenceBadge } from './EvidenceBadge';
import { ThemeList } from './ThemeList';

export function LabCard({
  lab,
  campusSelection = 'all',
}: {
  lab: PublicLab;
  campusSelection?: CampusSelection;
}) {
  const campusEvidence = evidenceForCampus(lab, campusSelection);
  const campusSummary =
    campusSelection === 'all' || campusSelection === 'unspecified'
      ? null
      : (lab.campus_summaries.find((item) => item.campus_id === campusSelection) ?? null);
  const effectiveSummary = campusSummary?.summary ?? lab.summary;
  const effectiveProvenance = campusSummary?.provenance ?? lab.provenance;
  const effectiveConfidence = campusSummary?.confidence ?? lab.confidence;

  if (!lab.has_summary || !effectiveSummary) {
    return (
      <article className="lab lab--insufficient" aria-label={lab.lab_name}>
        <div className="lab__head">
          <div>
            <div className="lab__name">{lab.lab_name}</div>
            <div className="lab__dept">{lab.department}</div>
          </div>
        </div>
        <p className="small muted" style={{ margin: '8px 0 0' }}>
          {lab.message ?? 'Insufficient public data for a reliable summary.'}
        </p>
        {(campusEvidence || lab.provenance) && (
          <div style={{ marginTop: 8 }}>
            <EvidenceBadge
              items={campusEvidence?.source_item_count ?? lab.provenance?.source_item_count ?? 0}
              authors={
                campusEvidence?.unique_author_count ?? lab.provenance?.unique_author_count ?? 0
              }
              withheld={campusSelection === 'all' ? (lab.provenance?.withheld_item_count ?? 0) : 0}
            />
          </div>
        )}
      </article>
    );
  }

  const summary = effectiveSummary;
  const provenance = effectiveProvenance;
  return (
    <article className="lab" aria-label={lab.lab_name}>
      <div className="lab__head">
        <div>
          <div className="lab__name">{lab.lab_name}</div>
          <div className="lab__dept">{lab.department}</div>
        </div>
        <ConfidenceIndicator level={effectiveConfidence} />
      </div>

      {campusSelection !== 'all' && (
        <p className="small muted" style={{ margin: '8px 0 0' }}>
          {campusSummary
            ? 'Location-specific summary (threshold independently met).'
            : 'Institution-wide lab summary; the evidence count below is location-specific.'}
        </p>
      )}

      {lab.research_areas.length > 0 && (
        <div className="chip-row" style={{ marginTop: 8 }}>
          {lab.research_areas.map((area) => (
            <span className="chip" key={area}>
              {area}
            </span>
          ))}
        </div>
      )}

      <p style={{ margin: '12px 0' }}>{summary.overview}</p>

      <ThemeList title="Recurring positive themes" themes={summary.positive_themes} />
      <ThemeList title="Recurring challenges" themes={summary.challenge_themes} />

      {summary.neutral_observations.length > 0 && (
        <div className="theme-group">
          <div className="theme-group__title">Neutral observations</div>
          <ul className="limitations">
            {summary.neutral_observations.map((obs) => (
              <li key={obs}>{obs}</li>
            ))}
          </ul>
        </div>
      )}

      {summary.limitations.length > 0 && (
        <div className="theme-group">
          <div className="theme-group__title">Limitations</div>
          <ul className="limitations">
            {summary.limitations.map((limit) => (
              <li key={limit}>{limit}</li>
            ))}
          </ul>
        </div>
      )}

      <div
        className="chip-row"
        style={{ marginTop: 12, justifyContent: 'space-between', alignItems: 'center' }}
      >
        {(campusEvidence || provenance) && (
          <EvidenceBadge
            items={campusEvidence?.source_item_count ?? provenance?.source_item_count ?? 0}
            authors={campusEvidence?.unique_author_count ?? provenance?.unique_author_count ?? 0}
            withheld={campusSelection === 'all' ? (provenance?.withheld_item_count ?? 0) : 0}
          />
        )}
        {(campusEvidence || provenance) && (
          <span className="small muted">
            {formatDateRange(
              campusEvidence?.date_range_start ?? provenance?.date_range_start ?? null,
              campusEvidence?.date_range_end ?? provenance?.date_range_end ?? null,
            )}
          </span>
        )}
      </div>

      <PerceptionsNote />
    </article>
  );
}
