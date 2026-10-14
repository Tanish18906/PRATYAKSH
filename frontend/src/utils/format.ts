// Number formatting utilities (dates live in utils/names.ts)

export function formatNumber(n: number | null | undefined): string {
  if (n === null || n === undefined) return 'N/A';
  return n.toLocaleString('en-US');
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
