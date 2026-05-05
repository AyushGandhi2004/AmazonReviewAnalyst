import { Fragment } from 'react'
import ProductImage from './ProductImage'

/**
 * Side-by-side specification comparison driven by `section_3.comparison_table`.
 *
 * Properties already covered by the head-to-head metrics grid (Rating, Review
 * Count, Price, BSR) are filtered out so this section is complementary, not
 * duplicative.
 *
 * Layouts:
 *   - mobile: one card per property with value pairs underneath
 *   - md+:    a single grid table with image-styled product headers
 */

const SKIP_PROPERTIES = new Set([
  'rating',
  'star rating',
  'review count',
  'reviews',
  'total reviews',
  'price',
  'bsr',
  'best sellers rank',
])

function filterRows(table) {
  return (table ?? []).filter(row => !SKIP_PROPERTIES.has(row.property.trim().toLowerCase()))
}

function orderProducts(products, yourAsin, fallbackAsins) {
  if (products?.length) {
    return [
      ...products.filter(p => p.asin === yourAsin),
      ...products.filter(p => p.asin !== yourAsin),
    ]
  }
  // Fallback when section_1.products is missing — synthesize stub products from
  // the ASIN keys present in the table values.
  return fallbackAsins.map(asin => ({ asin, title: asin, image_url: null }))
}

function valuesDiffer(values) {
  const list = Object.values(values).filter(v => v != null && v !== '')
  if (list.length < 2) return false
  return new Set(list.map(v => String(v).trim().toLowerCase())).size > 1
}

// ─────────────────────────────────────────────────────────
// Mobile: per-property card
// ─────────────────────────────────────────────────────────

function MobilePropertyCard({ row, ordered, yourAsin, delay }) {
  const differs = valuesDiffer(row.values)

  return (
    <article
      className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 animate-fade-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-baseline justify-between mb-3">
        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-400 font-semibold">
          {row.property}
        </p>
        {differs && (
          <span className="text-[10px] uppercase tracking-[0.14em] text-amber-600 font-semibold">
            Differs
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-3">
        {ordered.map(p => {
          const isYours = p.asin === yourAsin
          const value = row.values[p.asin]
          return (
            <div
              key={p.asin}
              className={`rounded-xl p-3 ${
                isYours ? 'bg-indigo-50/40 ring-1 ring-indigo-100' : 'bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <ProductImage src={p.image_url} alt="" size="sm" />
                <span
                  className={`text-[10px] uppercase tracking-[0.14em] font-bold ${
                    isYours ? 'text-indigo-700' : 'text-slate-500'
                  }`}
                >
                  {isYours ? 'You' : 'Them'}
                </span>
              </div>
              <p className="text-sm font-medium text-slate-900 leading-snug wrap-break-word">
                {value || <span className="text-slate-300">—</span>}
              </p>
            </div>
          )
        })}
      </div>
    </article>
  )
}

// ─────────────────────────────────────────────────────────
// Desktop: header cell
// ─────────────────────────────────────────────────────────

function HeaderCell({ product, isYours, delay }) {
  return (
    <div
      className={`rounded-xl p-3 transition animate-fade-up ${
        isYours
          ? 'bg-white border border-indigo-300 ring-1 ring-indigo-100'
          : 'bg-white border border-slate-200'
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center gap-3">
        <ProductImage src={product.image_url} alt="" size="md" />
        <div className="min-w-0">
          {isYours ? (
            <span className="inline-flex items-center bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-0.5 rounded-full mb-1">
              Your product
            </span>
          ) : (
            <span className="inline-flex items-center bg-slate-100 text-slate-500 text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-0.5 rounded-full mb-1">
              Competitor
            </span>
          )}
          <p className="font-mono text-[10px] text-slate-400">{product.asin}</p>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────

export default function SpecComparison({ table, products, yourAsin }) {
  const rows = filterRows(table)
  if (!rows.length) return null

  // Collect every ASIN referenced by the table so we can fall back even if
  // section_1.products is somehow empty.
  const fallbackAsins = Array.from(
    new Set(rows.flatMap(r => Object.keys(r.values))),
  )

  const ordered = orderProducts(products, yourAsin, fallbackAsins)
  if (!ordered.length) return null

  const labelCol = '180px'
  const productColCount = ordered.length
  const minColWidth = '200px'
  const gridTemplate = `${labelCol} repeat(${productColCount}, minmax(${minColWidth}, 1fr))`

  return (
    <section>
      <div className="flex items-baseline justify-between mb-5 sm:mb-6 gap-3 flex-wrap">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold mb-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
            Spec face-off
          </p>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Side-by-side specifications
          </h2>
        </div>
        <span className="text-xs text-slate-400 tabular-nums">
          {rows.length} propert{rows.length === 1 ? 'y' : 'ies'}
        </span>
      </div>

      {/* ── Mobile ──────────────────────────────────────────── */}
      <div className="md:hidden space-y-3">
        {rows.map((row, i) => (
          <MobilePropertyCard
            key={row.property}
            row={row}
            ordered={ordered}
            yourAsin={yourAsin}
            delay={i * 40}
          />
        ))}
      </div>

      {/* ── Desktop ─────────────────────────────────────────── */}
      <div className="hidden md:block">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 lg:p-7 overflow-x-auto scrollbar-thin">
          <div
            className="grid gap-x-4 gap-y-3 sm:gap-x-5 items-stretch min-w-[640px]"
            style={{ gridTemplateColumns: gridTemplate }}
          >
            {/* Header row */}
            <div className="flex items-end pb-2">
              <span className="text-[11px] uppercase tracking-[0.18em] text-slate-400 font-semibold">
                Spec
              </span>
            </div>
            {ordered.map((p, i) => (
              <HeaderCell
                key={p.asin}
                product={p}
                isYours={p.asin === yourAsin}
                delay={i * 50}
              />
            ))}

            {/* Data rows */}
            {rows.map((row, ri) => {
              const differs = valuesDiffer(row.values)
              return (
                <Fragment key={row.property}>
                  <div className="flex items-center pl-1 py-2 self-stretch">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-700 leading-snug">{row.property}</p>
                      {differs && (
                        <p className="text-[10px] uppercase tracking-[0.14em] text-amber-600 font-semibold mt-0.5">
                          Differs
                        </p>
                      )}
                    </div>
                  </div>
                  {ordered.map((p, i) => {
                    const isYours = p.asin === yourAsin
                    const value = row.values[p.asin]
                    return (
                      <div
                        key={p.asin}
                        className={`rounded-xl px-4 py-3 transition animate-fade-up self-stretch flex items-center ${
                          isYours
                            ? 'bg-indigo-50/30'
                            : 'bg-slate-50/60'
                        }`}
                        style={{ animationDelay: `${100 + ri * 30 + i * 30}ms` }}
                      >
                        <p className="text-sm text-slate-900 leading-snug wrap-break-word">
                          {value || <span className="text-slate-300">—</span>}
                        </p>
                      </div>
                    )
                  })}
                </Fragment>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
