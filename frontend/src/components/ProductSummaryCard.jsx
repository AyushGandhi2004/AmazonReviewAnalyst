import ProductImage from './ProductImage'

/**
 * Per-product card used inside the tabbed Strengths/Weaknesses comparison.
 *
 * The parent passes a `lens` prop telling this card which list to render
 * (strengths / weaknesses / top_praises / top_complaints). The "overall
 * reaction" pull-quote is always visible at the top — it's the most
 * compressed form of the per-product narrative.
 */

const LENS_CONFIG = {
  strengths: {
    key: 'strengths',
    pillBase: 'bg-emerald-50 text-emerald-700 border border-emerald-100',
    accent: 'emerald',
    emptyText: 'No strengths surfaced.',
  },
  weaknesses: {
    key: 'weaknesses',
    pillBase: 'bg-rose-50 text-rose-700 border border-rose-100',
    accent: 'rose',
    emptyText: 'No weaknesses surfaced.',
  },
  top_praises: {
    key: 'top_praises',
    pillBase: 'bg-sky-50 text-sky-700 border border-sky-100',
    accent: 'sky',
    emptyText: 'No standout praise.',
  },
  top_complaints: {
    key: 'top_complaints',
    pillBase: 'bg-amber-50 text-amber-700 border border-amber-100',
    accent: 'amber',
    emptyText: 'No common complaints.',
  },
}

export default function ProductSummaryCard({ summary, isYours, lens = 'strengths', imageUrl }) {
  const config = LENS_CONFIG[lens] ?? LENS_CONFIG.strengths
  const items = summary?.[config.key] ?? []

  return (
    <div
      className={`relative bg-white rounded-2xl border p-5 sm:p-6 transition hover:shadow-sm flex flex-col gap-4 ${
        isYours ? 'border-indigo-300 ring-1 ring-indigo-100' : 'border-slate-200'
      }`}
    >
      {/* Header */}
      <div>
        <div className="flex items-start gap-3 mb-3">
          <ProductImage src={imageUrl} alt={summary.product_title} size="md" />
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2 mb-1">
              {isYours ? (
                <span className="inline-flex items-center bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-0.5 rounded-full">
                  Your product
                </span>
              ) : (
                <span className="inline-flex items-center bg-slate-100 text-slate-500 text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-0.5 rounded-full">
                  Competitor
                </span>
              )}
              <span className="font-mono text-[10px] text-slate-400">{summary.asin}</span>
            </div>
            <h3 className="font-semibold text-slate-900 text-sm leading-snug line-clamp-2">
              {summary.product_title}
            </h3>
          </div>
        </div>
        {summary.overall_reaction && (
          <p className="text-slate-600 text-xs sm:text-[13px] leading-relaxed border-l-2 border-slate-200 pl-3 italic">
            {summary.overall_reaction}
          </p>
        )}
      </div>

      {/* Lens content */}
      <div
        key={lens}
        className="flex flex-wrap gap-1.5 animate-fade-in min-h-[2.5rem]"
      >
        {items.length ? (
          items.map((item, i) => (
            <span
              key={i}
              className={`text-xs px-2.5 py-1 pb-1 rounded-lg leading-snug ${config.pillBase}`}
            >
              {item}
            </span>
          ))
        ) : (
          <span className="text-xs text-slate-400">{config.emptyText}</span>
        )}
      </div>

      {/* Footer count */}
      <div className="border-t border-slate-100 pt-2.5 flex items-center justify-between">
        <span className="text-[11px] text-slate-400 capitalize">
          {lens.replace('_', ' ')}
        </span>
        <span className="text-[11px] font-semibold text-slate-600 tabular-nums">
          {items.length}
        </span>
      </div>
    </div>
  )
}
