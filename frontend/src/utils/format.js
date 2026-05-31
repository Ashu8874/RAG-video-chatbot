export function formatNum(n) {
  if (!n && n !== 0) return '—'
  n = Number(n)
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return n.toLocaleString()
}

export function formatDuration(seconds) {
  if (!seconds) return '—'
  const s = Number(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
  return `${m}:${String(sec).padStart(2,'0')}`
}

export function formatDate(raw) {
  if (!raw || raw === 'Unknown') return '—'
  if (/^\d{8}$/.test(raw)) {
    const y = raw.slice(0,4), mo = raw.slice(4,6), d = raw.slice(6,8)
    return `${d}/${mo}/${y}`
  }
  try { return new Date(raw).toLocaleDateString('en-IN') } catch { return raw }
}

export function engagementColor(rate) {
  const r = parseFloat(rate)
  if (!Number.isFinite(r)) return '#64748b'
  if (r >= 5) return '#22c55e'
  if (r >= 2) return '#eab308'
  return '#ef4444'
}
