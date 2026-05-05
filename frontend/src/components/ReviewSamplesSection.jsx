/**
 * Voice of customer — tabbed by product, with 5★ and 1★ side by side.
 * Compact and dense; the tab switch animates with a fade-in only.
 */

import { useState, useMemo } from 'react'
import ProductImage from './ProductImage'

function StarRow({ rating, color }) {
  return (
    <span className={`inline-flex items-center gap-px text-[11px] tabular-nums ${color}`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <svg key={i} className="w-3 h-3" viewBox="0 0 20 20" fill={i < rating ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={1.5}>
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </span>
  )
}

function ReviewCard({ review, tone }) {
  const palette =
    tone === 'love'
      ? {
          bg: 'bg-emerald-50/40',
          border: 'border-emerald-100',
          star: 'text-emerald-500',
          chip: 'text-emerald-700 bg-emerald-100/70',
        }
      : {
          bg: 'bg-rose-50/40',
          border: 'border-rose-100',
          star: 'text-rose-500',
          chip: 'text-rose-700 bg-rose-100/70',
        }

  return (
    <article className={`rounded-xl border ${palette.border} ${palette.bg} p-3.5 transition hover:bg-white`}>
      <header className="flex items-center gap-2 mb-1.5 flex-wrap">
        <StarRow rating={review.rating} color={palette.star} />
        {review.verified_purchase && (
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${palette.chip}`}>
            ✓ Verified
          </span>
        )}
        {review.date && (
          <span className="text-[10px] text-slate-400 ml-auto">{review.date}</span>
        )}
      </header>
      {review.title && (
        <p className="font-semibold text-slate-800 text-xs mb-1 leading-snug">{review.title}</p>
      )}
      <p className="text-slate-600 text-xs leading-relaxed line-clamp-5">{review.text}</p>
    </article>
  )
}

function ReviewColumn({ title, count, reviews, tone, emptyText }) {
  const heading = tone === 'love' ? 'text-emerald-700' : 'text-rose-700'
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <h4 className={`font-semibold text-[11px] uppercase tracking-wider ${heading}`}>{title}</h4>
        <span className="text-[11px] text-slate-400 tabular-nums">{count}</span>
      </div>
      {reviews?.length ? (
        <div className="space-y-2.5">
          {reviews.map((r, i) => (
            <ReviewCard key={i} review={r} tone={tone} />
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-400">{emptyText}</p>
      )}
    </div>
  )
}

export default function ReviewSamplesSection({ samples, yourAsin, imagesByAsin = {} }) {
  const ordered = useMemo(() => {
    if (!samples?.length) return []
    return [
      ...samples.filter(s => s.asin === yourAsin),
      ...samples.filter(s => s.asin !== yourAsin),
    ]
  }, [samples, yourAsin])

  const [activeAsin, setActiveAsin] = useState(ordered[0]?.asin)
  const active = ordered.find(s => s.asin === activeAsin) ?? ordered[0]

  if (!ordered.length) {
    return (
      <section>
        <h2 className="text-xl font-bold text-slate-900 mb-4 tracking-tight">Voice of customer</h2>
        <p className="text-slate-400 text-sm">No review samples available.</p>
      </section>
    )
  }

  return (
    <section>
      <div className="flex items-baseline justify-between mb-5 sm:mb-6 gap-3 flex-wrap">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold mb-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
            Voice of customer
          </p>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            What buyers actually say
          </h2>
        </div>
        <span className="text-xs text-slate-400 tabular-nums">
          {(active?.five_star?.length ?? 0) + (active?.one_star?.length ?? 0)} samples shown
        </span>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
        {/* Product tabs */}
        <div className="border-b border-slate-100 px-2 sm:px-3 overflow-x-auto scrollbar-thin">
          <div className="flex items-center gap-1 min-w-max">
            {ordered.map(s => {
              const isActive = s.asin === active?.asin
              const isYours = s.asin === yourAsin
              return (
                <button
                  key={s.asin}
                  onClick={() => setActiveAsin(s.asin)}
                  className={`relative px-3 py-3 text-xs font-medium transition whitespace-nowrap ${
                    isActive ? 'text-slate-900' : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <ProductImage src={imagesByAsin[s.asin]} alt="" size="sm" />
                    <span className="flex flex-col items-start leading-tight">
                      <span className="flex items-center gap-1.5">
                        {isYours && (
                          <span className="inline-flex items-center bg-indigo-50 text-indigo-700 text-[9px] font-bold uppercase tracking-[0.14em] px-1.5 py-0.5 rounded">
                            You
                          </span>
                        )}
                        <span className="font-mono text-[10px] text-slate-400">{s.asin}</span>
                      </span>
                      <span className="hidden md:inline max-w-[200px] truncate text-[12px] text-slate-700">
                        {s.product_title}
                      </span>
                    </span>
                  </span>
                  {isActive && (
                    <span className="absolute left-2 right-2 -bottom-px h-0.5 bg-indigo-500 rounded-full animate-fade-in" />
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Active panel */}
        {active && (
          <div key={active.asin} className="p-5 sm:p-6 animate-fade-in">
            <div className="flex items-center gap-3 mb-5 sm:mb-6">
              <ProductImage src={imagesByAsin[active.asin]} alt={active.product_title} size="md" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900 leading-snug line-clamp-1">
                  {active.product_title}
                </p>
                <p className="font-mono text-[10px] text-slate-400 mt-0.5">{active.asin}</p>
              </div>
            </div>
            <div className="grid gap-6 sm:gap-8 md:grid-cols-2">
              <ReviewColumn
                title="What lovers say"
                count={active.five_star?.length ?? 0}
                reviews={active.five_star}
                tone="love"
                emptyText="No 5-star samples."
              />
              <ReviewColumn
                title="What critics say"
                count={active.one_star?.length ?? 0}
                reviews={active.one_star}
                tone="hate"
                emptyText="No 1-star samples."
              />
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
