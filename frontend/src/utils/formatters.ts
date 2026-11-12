export function formatInt(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-'
  return value.toLocaleString('en-US')
}

export function formatDuration(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return '-'
  if (ms < 1000) return `${Math.round(ms)} ms`
  return `${(ms / 1000).toFixed(2)} s`
}

export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function shortChecksum(checksum: string | null | undefined): string {
  if (!checksum) return '-'
  return checksum.slice(0, 12)
}
