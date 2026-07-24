import type { Dataset, ExportMeta, PublicInstitution, Region } from '../types';

const base = import.meta.env.BASE_URL;

async function fetchJson<T>(file: string): Promise<T> {
  const response = await fetch(`${base}data/${file}`);
  if (!response.ok) {
    throw new Error(`Failed to load ${file} (HTTP ${response.status}).`);
  }
  return (await response.json()) as T;
}

export async function loadDataset(): Promise<Dataset> {
  const [regions, institutions, meta] = await Promise.all([
    fetchJson<Region[]>('regions.json'),
    fetchJson<PublicInstitution[]>('institutions.json'),
    fetchJson<ExportMeta>('meta.json'),
  ]);
  return { regions, institutions, meta };
}
