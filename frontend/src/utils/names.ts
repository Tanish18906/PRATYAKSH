// Display helpers: names instead of internal ids, plain dates (docs/ui-REDESIGN/UX_FLOW.md section 6)

import { Action } from '../types/contract';

// Only the parts of a scenario needed to resolve names
export interface NameSource {
  actors: Array<{ id: string; name: string }>;
  locations: Array<{ id: string; name: string }>;
}

const PREFIX_LABEL: Record<string, string> = {
  art: 'Export',
  hyp: 'Route',
  can: 'Canary',
  evt: 'Event',
};

const titleCase = (s: string) => s.replace(/[-_]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export function displayName(id: string | null | undefined, names?: NameSource | null): string {
  if (!id) return 'Unknown';
  const known = names?.actors.find((a) => a.id === id) ?? names?.locations.find((l) => l.id === id);
  if (known) return known.name;
  const i = id.indexOf(':');
  if (i < 0) return id;
  const prefix = id.slice(0, i);
  const rest = id.slice(i + 1);
  if (prefix === 'src') return `${titleCase(rest)} logs`;
  return PREFIX_LABEL[prefix] ? `${PREFIX_LABEL[prefix]} ${rest}` : titleCase(rest);
}

const ID_RE = /\b(art|act|sys|ep|ext|ch|ds|hyp|src|can|evt|trc|scn|leak|aud):[\w-]+/g;
const ISO_RE = /\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z\b/g;

// The engine's narrative text carries ids and ISO times; this makes it readable without changing its meaning
export function prettyIds(text: string, names?: NameSource | null): string {
  return text.replace(ID_RE, (id) => displayName(id, names)).replace(ISO_RE, (ts) => formatDay(ts));
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// "9 Oct, 21:40 UTC"
export function formatDay(iso: string | null | undefined): string {
  if (!iso) return 'Time unknown';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}, ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
}

export const wholePercent = (p: number | null | undefined): string =>
  p === null || p === undefined ? 'N/A' : `${Math.round(p * 100)}%`;

export const ACTION_VERB: Record<Action, string> = {
  read: 'read',
  query: 'queried',
  export: 'exported',
  copy: 'copied',
  send: 'sent',
  upload: 'uploaded',
  download: 'downloaded',
  api_call: 'API call',
  permission_change: 'permission change',
};
