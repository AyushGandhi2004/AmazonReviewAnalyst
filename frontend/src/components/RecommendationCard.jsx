/**
 * Single recommendation card. Visual priority = left accent bar.
 * Area is shown as a small monochrome chip — the priority is the loud signal.
 */

const PRIORITY = {
  high: {
    badge: 'bg-rose-50 text-rose-700 ring-rose-200',
    bar: 'bg-rose-400',
    label: 'High',
    glow: 'shadow-[0_0_0_1px_rgba(244,63,94,0.08)]',
  },
  medium: {
    badge: 'bg-amber-50 text-amber-700 ring-amber-200',
    bar: 'bg-amber-400',
    label: 'Medium',
    glow: '',
  },
  low: {
    badge: 'bg-slate-100 text-slate-600 ring-slate-200',
    bar: 'bg-slate-300',
    label: 'Low',
    glow: '',
  },
}

const AREA = {
  product: { chip: 'bg-violet-50 text-violet-700 border-violet-100', icon: '⌖' },
  listing: { chip: 'bg-sky-50 text-sky-700 border-sky-100', icon: '✎' },
  pricing: { chip: 'bg-teal-50 text-teal-700 border-teal-100', icon: '$' },
}

export default function RecommendationCard({ recommendation: rec, index }) {
  const priority = PRIORITY[rec.priority] ?? PRIORITY.low
  const area = AREA[rec.area] ?? { chip: 'bg-slate-50 text-slate-600 border-slate-100', icon: '•' }

  return (
    <div
      className={`group relative bg-white rounded-2xl border border-slate-200 overflow-hidden transition hover:border-slate-300 ${priority.glow}`}
    >
      {/* Left priority bar */}
      <span className={`absolute left-0 top-0 bottom-0 w-1 ${priority.bar}`} />

      <div className="pl-5 pr-5 py-4 flex gap-4 items-start">
        {/* Index */}
        {index != null && (
          <span className="flex-shrink-0 text-slate-300 text-xs font-mono tabular-nums pt-0.5 select-none">
            {String(index + 1).padStart(2, '0')}
          </span>
        )}

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span
              className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ring-1 ${priority.badge}`}
            >
              {priority.label}
            </span>
            <span
              className={`inline-flex items-center gap-1 text-[10px] font-semibold capitalize px-2 py-0.5 rounded-full border ${area.chip}`}
            >
              <span className="opacity-70">{area.icon}</span>
              {rec.area}
            </span>
          </div>
          <p className="font-semibold text-slate-900 text-sm leading-snug mb-1">
            {rec.action}
          </p>
          <p className="text-slate-500 text-xs leading-relaxed">{rec.rationale}</p>
        </div>
      </div>
    </div>
  )
}
