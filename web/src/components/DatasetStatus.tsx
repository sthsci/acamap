import type { ExportMeta } from '../types';

interface Props {
  meta: ExportMeta;
}

export function DatasetStatus({ meta }: Props) {
  const isDemo = meta.dataset_kind === 'synthetic_demo';
  return (
    <div
      className={`dataset-status dataset-status--${isDemo ? 'demo' : 'imported'}`}
      role="status"
      aria-label="Dataset status"
    >
      <div>
        <strong>{isDemo ? 'Demonstration dataset' : 'Sanitised public-data aggregates'}</strong>
        <p>{meta.dataset_note}</p>
      </div>
      <dl>
        <div>
          <dt>Evidence items</dt>
          <dd>{meta.total_source_items}</dd>
        </div>
        <div>
          <dt>Published lab summaries</dt>
          <dd>{meta.published_lab_count}</dd>
        </div>
      </dl>
    </div>
  );
}
