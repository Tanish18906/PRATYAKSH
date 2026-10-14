// Deterministic UTC and numerical formatting utilities
// Follows rules in docs/FRONTEND.md section 16 and docs/UI_UX_DESIGN.md

export function formatUtcTime(isoString: string | null | undefined): string {
  if (!isoString) {
    return 'Time unavailable';
  }
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) {
      return isoString;
    }
    const pad = (n: number) => String(n).padStart(2, '0');
    const yyyy = d.getUTCFullYear();
    const mm = pad(d.getUTCMonth() + 1);
    const dd = pad(d.getUTCDate());
    const hh = pad(d.getUTCHours());
    const min = pad(d.getUTCMinutes());
    const ss = pad(d.getUTCSeconds());
    return `${yyyy}-${mm}-${dd} ${hh}:${min}:${ss} UTC`;
  } catch {
    return 'Time unavailable';
  }
}

export function formatUtcShort(isoString: string | null | undefined): string {
  if (!isoString) {
    return 'Time unavailable';
  }
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const pad = (n: number) => String(n).padStart(2, '0');
    const mm = pad(d.getUTCMonth() + 1);
    const dd = pad(d.getUTCDate());
    const hh = pad(d.getUTCHours());
    const min = pad(d.getUTCMinutes());
    return `${mm}-${dd} ${hh}:${min}Z`;
  } catch {
    return 'Time unavailable';
  }
}

export function formatNumber(n: number | null | undefined): string {
  if (n === null || n === undefined) return 'N/A';
  return n.toLocaleString('en-US');
}

export function formatProbability(p: number | null | undefined): string {
  if (p === null || p === undefined) return 'N/A';
  return `${(p * 100).toFixed(1)}%`;
}

export function formatScore(s: number | null | undefined): string {
  if (s === null || s === undefined) return 'N/A';
  return s.toFixed(4);
}

export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}
