import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

// Guards the JSON that ships in the build. Mirrors the pipeline's privacy scan
// so a leak fails the frontend test suite too, independent of Python.

const FORBIDDEN_KEYS = new Set([
  'username',
  'userid',
  'user',
  'handle',
  'nickname',
  'authorid',
  'authorname',
  'authorhash',
  'author',
  'realname',
  'researchername',
  'email',
  'postid',
  'posthash',
  'commentid',
  'commenthash',
  'profileurl',
  'profile',
  'sourceurl',
  'text',
  'rawtext',
  'body',
  'content',
  'comment',
  'comments',
  'postedat',
  'collectedat',
  'campusnameraw',
  'campusassignmentmethod',
  'campusassignmentconfidence',
]);

const SUSPICIOUS_URL = /(xiaohongshu|xhslink|rednote|\/user\/|\/profile|\/u\/|@)/i;

function normalise(key: string): string {
  return key.toLowerCase().replace(/[^a-z0-9]/g, '');
}

function scan(value: unknown, path = '$'): string[] {
  const findings: string[] = [];
  if (Array.isArray(value)) {
    value.forEach((item, i) => findings.push(...scan(item, `${path}[${i}]`)));
  } else if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) {
      if (FORBIDDEN_KEYS.has(normalise(key))) {
        findings.push(`${path}.${key}: forbidden key`);
      }
      findings.push(...scan(child, `${path}.${key}`));
    }
  } else if (typeof value === 'string') {
    if (/^https?:\/\//i.test(value) && SUSPICIOUS_URL.test(value)) {
      findings.push(`${path}: suspicious url`);
    }
  }
  return findings;
}

function loadPublic(file: string): unknown {
  // Vitest runs with the web/ package directory as its working directory.
  const path = join(process.cwd(), 'public', 'data', file);
  return JSON.parse(readFileSync(path, 'utf-8'));
}

const files = ['institutions.json', 'regions.json', 'meta.json'];

describe('shipped public data', () => {
  it.each(files)('%s exists and parses', (file) => {
    expect(loadPublic(file)).toBeTruthy();
  });

  it.each(files)('%s contains no forbidden keys or identifying URLs', (file) => {
    expect(scan(loadPublic(file))).toEqual([]);
  });

  it('has one map marker per campus with coordinates and region', () => {
    const institutions = loadPublic('institutions.json') as Array<Record<string, unknown>>;
    expect(institutions.length).toBeGreaterThan(0);
    for (const inst of institutions) {
      expect(typeof inst.region).toBe('string');
      expect(Array.isArray(inst.campuses)).toBe(true);
      for (const campus of inst.campuses as Array<Record<string, unknown>>) {
        expect(typeof campus.latitude).toBe('number');
        expect(typeof campus.longitude).toBe('number');
        expect(typeof campus.campus_id).toBe('string');
      }
    }
  });
});
