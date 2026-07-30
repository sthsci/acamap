// Types mirror the sanitised JSON produced by the Python pipeline's export step.
// The public payload contains NO raw text, usernames, identifiers or URLs.

export type Confidence = 'low' | 'medium' | 'high';
export type RegionStatus = 'active' | 'coming_soon';
export type CampusSelection = 'all' | 'unspecified' | string;
export type CampusLocationType =
  'university_campus' | 'medical_research_campus' | 'research_institute' | 'research_location';
export type EvidenceStatus = 'summary_available' | 'below_threshold' | 'no_assigned_evidence';

export interface Theme {
  theme: string;
  description: string;
  supporting_item_count: number;
}

export interface LlmSummary {
  overview: string;
  positive_themes: Theme[];
  challenge_themes: Theme[];
  neutral_observations: string[];
  confidence: Confidence;
  limitations: string[];
  withheld_item_count: number;
}

export interface Provenance {
  source_item_count: number;
  unique_author_count: number;
  withheld_item_count: number;
  date_range_start: string | null;
  date_range_end: string | null;
  generated_at: string;
  model: string;
}

export interface PublicLab {
  lab_id: string;
  lab_name: string;
  department: string;
  campus_ids: string[];
  campus_evidence: PublicCampusEvidence[];
  campus_summaries: PublicCampusLabSummary[];
  research_areas: string[];
  has_summary: boolean;
  message: string | null;
  confidence: Confidence | null;
  provenance: Provenance | null;
  summary: LlmSummary | null;
}

export interface PublicCampusEvidence {
  campus_id: string | null;
  campus_label: string;
  source_item_count: number;
  unique_author_count: number;
  date_range_start: string | null;
  date_range_end: string | null;
}

export interface PublicCampusLabSummary {
  campus_id: string;
  confidence: Confidence;
  provenance: Provenance;
  summary: LlmSummary;
}

export interface PublicCampus {
  campus_id: string;
  name: string;
  short_name: string;
  latitude: number;
  longitude: number;
  address: string;
  location_type: CampusLocationType;
  represented_lab_count: number;
  source_item_count: number;
  unique_author_count: number;
  evidence_status: EvidenceStatus;
  confidence: Confidence | null;
  provenance: Provenance | null;
  summary: LlmSummary | null;
}

export interface PublicInstitution {
  institution_id: string;
  name: string;
  short_name: string;
  region: string;
  map_center: { latitude: number; longitude: number };
  website: string | null;
  campuses: PublicCampus[];
  campus_unspecified: PublicCampusEvidence;
  represented_lab_count: number;
  source_item_count: number;
  unique_author_count: number;
  date_range_start: string | null;
  date_range_end: string | null;
  overall_themes: string[];
  confidence: Confidence | null;
  last_updated: string | null;
  departments: string[];
  research_areas: string[];
  labs: PublicLab[];
}

export interface Region {
  id: string;
  name: string;
  status: RegionStatus;
  center: [number, number];
  zoom: number;
}

export interface ExportMeta {
  generated_at: string;
  model: string;
  prompt_version: string;
  min_items: number;
  min_authors: number;
  institution_count: number;
  published_lab_count: number;
  withheld_lab_count: number;
  total_source_items: number;
  dataset_kind: 'synthetic_demo' | 'lawfully_imported';
  dataset_note: string;
  disclaimer: string;
}

export interface Dataset {
  regions: Region[];
  institutions: PublicInstitution[];
  meta: ExportMeta;
}
