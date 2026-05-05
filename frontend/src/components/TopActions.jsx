/**
 * "Do these first" — the 3 most urgent actions, displayed as a horizontal row
 * of cards. Sits between the verdict and the head-to-head metrics. Acts as a
 * preview of the full Action Plan section further down the page.
 */

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 }

const PRIORITY_TONE = {
  high: { dot: 'bg-rose-500', label: 'High', text: 'text-rose-700' },
  medium: { dot: 'bg-amber-500', label: 'Medium', text: 'text-amber-700' },
  low: { dot: 'bg-slate-400', label: 'Low', text: 'text-slate-600' },
}

const AREA_LABEL = {
  product: 'Product',
  listing: 'Listing',
  pricing: 'Pricing',
}

function ActionCard({ rec, index, delay }) {
  const tone = PRIORITY_TONE[rec.priority] ?? PRIORITY_TONE.low

  return (
    <article
      className="group bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 hover:border-slate-300 transition animate-fade-up flex flex-col h-full"
      style={{ animationDelay: `${delay}ms` }}
    >
      <header className="flex items-center justify-between mb-3 sm:mb-4">
        <span className="text-[10px] uppercase tracking-[0.18em] text-slate-400 font-semibold tabular-nums">
          {String(index + 1).padStart(2, '0')}
        </span>
        <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold">
          <span className={`w-1.5 h-1.5 rounded-full ${tone.dot}`} />
          <span className={tone.text}>{tone.label}</span>
          <span className="text-slate-300">·</span>
          <span className="text-slate-500">{AREA_LABEL[rec.area] ?? rec.area}</span>
        </span>
      </header>

      <p className="font-semibold text-slate-900 text-sm sm:text-base leading-snug mb-2">
        {rec.action}
      </p>
      <p className="text-slate-500 text-xs sm:text-[13px] leading-relaxed line-clamp-3">
        {rec.rationale}
      </p>
    </article>
  )
}

export default function TopActions({ recommendations, anchor = '#action-plan', limit = 3 }) {
  const top = [...(recommendations ?? [])]
    .sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 3) - (PRIORITY_ORDER[b.priority] ?? 3))
    .slice(0, limit)

  if (!top.length) return null

  const total = recommendations.length

  return (
    <section className="space-y-5 sm:space-y-6">
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold mb-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-rose-500 rounded-full" />
            Do these first
          </p>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Three priorities for the next sprint
          </h2>
        </div>
        <a
          href={anchor}
          className="text-xs sm:text-sm text-indigo-600 hover:text-indigo-700 font-medium whitespace-nowrap"
        >
          See all {total} action{total === 1 ? '' : 's'} →
        </a>
      </div>

      <div className="grid gap-4 sm:gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {top.map((rec, i) => (
          <ActionCard key={i} rec={rec} index={i} delay={i * 80} />
        ))}
      </div>
    </section>
  )
}
