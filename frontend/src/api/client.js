const BASE = 'https://amazonreviewanalyst-backend.onrender.com'

export async function startAnalysis(yourAsin, competitorAsins) {
  const res = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      your_asin: yourAsin,
      competitor_asins: competitorAsins.filter(a => a.trim()),
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const detail = err.detail
    if (Array.isArray(detail)) {
      throw new Error(detail.map(d => d.msg || d).join('; '))
    }
    throw new Error(detail || `Request failed (HTTP ${res.status})`)
  }
  return res.json()
}

export function openProgressStream(runId) {
  return new EventSource(`${BASE}/progress/${runId}`)
}

export async function fetchReport(runId) {
  const res = await fetch(`${BASE}/report/${runId}`)
  if (res.status === 202) return null  // still in progress
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function pdfUrl(runId) {
  return `${BASE}/report/${runId}/pdf`
}
