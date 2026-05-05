import ProductImage from './ProductImage'
import InfoTip from './InfoTip'

/**
 * Head-to-head metrics across all products.
 *
 * Two layouts:
 *   - Mobile: each product gets its own card with metrics stacked vertically
 *   - md+:    a single grid "table" with one column per product
 *
 * In both layouts the winning value for each metric gets an emerald tint
 * + "Best" indicator. BSR is excluded from winner highlighting because
 * cross-category BSR comparisons are not meaningful.
 */

function parsePrice(raw) {
  if (!raw) return null
  const num = parseFloat(String(raw).replace(/[^0-9.]/g, ''))
  return Number.isFinite(num) ? num : null
}

function bestIndex(values, mode) {
  const valid = values.map((v, i) => ({ v, i })).filter(({ v }) => v != null && Number.isFinite(v))
  if (!valid.length) return -1
  const winner = valid.reduce((best, cur) =>
    mode === 'min' ? (cur.v < best.v ? cur : best) : (cur.v > best.v ? cur : best),
  )
  const allEqual = valid.every(({ v }) => v === winner.v)
  return allEqual ? -1 : winner.i
}

function relativeFraction(value, values, mode) {
  const valid = values.filter(v => v != null && Number.isFinite(v))
  if (!valid.length || value == null) return 0
  if (mode === 'min') {
    const max = Math.max(...valid)
    if (max === 0) return 0
    return Math.min(1, (max - value) / max + 0.15)
  }
  const max = Math.max(...valid)
  return max === 0 ? 0 : value / max
}

const STAR = (
  <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
)

const BEST_BADGE = (
  <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-[0.12em] text-emerald-700">
    <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
    Best
  </span>
)

function Bar({ fraction, tone }) {
  const toneClass = {
    emerald: 'bg-emerald-500',
    indigo: 'bg-indigo-400',
    slate: 'bg-slate-300',
    amber: 'bg-amber-400',
  }[tone] ?? 'bg-slate-300'
  return (
    <div className="mt-2.5 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
      <div
        className={`h-full ${toneClass} rounded-full origin-left animate-bar-fill`}
        style={{ transform: `scaleX(${Math.max(0.05, fraction)})` }}
      />
    </div>
  )
}

function Stars({ rating, fraction, tone }) {
  if (rating == null) return <span className="text-slate-300 text-sm">—</span>
  const full = Math.floor(rating)
  return (
    <>
      <div className="flex items-center gap-1.5">
        <span className="text-xl font-bold text-slate-900 tabular-nums leading-none">
          {rating.toFixed(1)}
        </span>
        <span className="flex">
          {Array.from({ length: 5 }).map((_, i) => (
            <span key={i} className={i < full ? 'text-amber-400' : 'text-slate-200'}>
              {STAR}
            </span>
          ))}
        </span>
      </div>
      <Bar fraction={fraction} tone={tone} />
    </>
  )
}

// ─────────────────────────────────────────────────────────
// Cell components
// ─────────────────────────────────────────────────────────

function PriceValue({ value, fraction, isWinner }) {
  return (
    <>
      <p className={`text-xl sm:text-2xl font-bold tabular-nums leading-none ${isWinner ? 'text-emerald-700' : 'text-slate-900'}`}>
        {value || <span className="text-slate-300">—</span>}
      </p>
      <Bar fraction={fraction} tone={isWinner ? 'emerald' : 'indigo'} />
    </>
  )
}

function ReviewsValue({ value, fraction, isWinner }) {
  return (
    <>
      <p className={`text-xl sm:text-2xl font-bold tabular-nums leading-none ${isWinner ? 'text-emerald-700' : 'text-slate-900'}`}>
        {value != null ? value.toLocaleString() : <span className="text-slate-300">—</span>}
      </p>
      <Bar fraction={fraction} tone={isWinner ? 'emerald' : 'indigo'} />
    </>
  )
}

function BsrValue({ value }) {
  if (!value) return <span className="text-slate-300 text-sm">—</span>
  return <p className="text-sm text-slate-700 leading-snug">{value}</p>
}

// ─────────────────────────────────────────────────────────
// Mobile: per-product cards
// ─────────────────────────────────────────────────────────

function MobileProductCard({
  product,
  isYours,
  delay,
  priceWin,
  ratingWin,
  reviewsWin,
  prices,
  ratings,
  reviewCounts,
  index,
}) {
  return (
    <article
      className={`bg-white rounded-2xl border p-5 transition animate-fade-up ${
        isYours ? 'border-indigo-300 ring-1 ring-indigo-100' : 'border-slate-200'
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <header className="flex items-start gap-4 mb-5">
        <ProductImage src={product.image_url} alt={product.title} size="lg" />
        <div className="min-w-0 flex-1">
          {isYours ? (
            <span className="inline-flex items-center bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-0.5 rounded-full mb-1.5">
              Your product
            </span>
          ) : (
            <span className="inline-flex items-center bg-slate-100 text-slate-500 text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-0.5 rounded-full mb-1.5">
              Competitor
            </span>
          )}
          <p className="text-sm font-semibold text-slate-900 leading-snug line-clamp-2">
            {product.title || product.asin}
          </p>
          <p className="font-mono text-[10px] text-slate-400 mt-1">{product.asin}</p>
        </div>
      </header>

      <dl className="grid grid-cols-2 gap-x-5 gap-y-5">
        <div>
          <dt className="text-[10px] uppercase tracking-[0.14em] text-slate-400 font-semibold mb-2 flex items-center justify-between">
            <span>Price</span>
            {priceWin && BEST_BADGE}
          </dt>
          <dd>
            <PriceValue
              value={product.price}
              fraction={relativeFraction(prices[index], prices, 'min')}
              isWinner={priceWin}
            />
          </dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-[0.14em] text-slate-400 font-semibold mb-2 flex items-center justify-between">
            <span>Rating</span>
            {ratingWin && BEST_BADGE}
          </dt>
          <dd>
            <Stars
              rating={ratings[index]}
              fraction={ratings[index] != null ? ratings[index] / 5 : 0}
              tone={ratingWin ? 'emerald' : 'amber'}
            />
          </dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-[0.14em] text-slate-400 font-semibold mb-2 flex items-center justify-between">
            <span>Reviews</span>
            {reviewsWin && BEST_BADGE}
          </dt>
          <dd>
            <ReviewsValue
              value={reviewCounts[index]}
              fraction={relativeFraction(reviewCounts[index], reviewCounts, 'max')}
              isWinner={reviewsWin}
            />
          </dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-[0.14em] text-slate-400 font-semibold mb-2 inline-flex items-center">
            BSR
            <InfoTip label="About BSR">
              Best Sellers Rank — Amazon's ranking within the product's primary category. Lower is better, but cross-category comparisons are not meaningful.
            </InfoTip>
          </dt>
          <dd>
            <BsrValue value={product.bsr} />
          </dd>
        </div>
      </dl>
    </article>
  )
}

// ─────────────────────────────────────────────────────────
// Desktop: comparison table
// ─────────────────────────────────────────────────────────

function ProductHeaderCell({ product, isYours, delay }) {
  return (
    <div
      className={`rounded-xl p-4 transition animate-fade-up ${
        isYours
          ? 'bg-white border border-indigo-300 ring-1 ring-indigo-100'
          : 'bg-white border border-slate-200'
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <ProductImage src={product.image_url} alt={product.title} size="lg" className="mb-3" />
      {isYours ? (
        <span className="inline-flex items-center bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-0.5 rounded-full mb-2">
          Your product
        </span>
      ) : (
        <span className="inline-flex items-center bg-slate-100 text-slate-500 text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-0.5 rounded-full mb-2">
          Competitor
        </span>
      )}
      <p className="font-semibold text-slate-900 text-xs sm:text-sm leading-snug line-clamp-2">
        {product.title || product.asin}
      </p>
      <p className="font-mono text-[10px] text-slate-400 mt-1">{product.asin}</p>
    </div>
  )
}

function MetricCell({ children, isWinner, isYours, delay = 0 }) {
  return (
    <div
      className={`relative rounded-xl px-4 py-4 sm:px-5 sm:py-5 transition animate-fade-up ${
        isWinner
          ? 'bg-emerald-50/60 ring-1 ring-emerald-200'
          : isYours
          ? 'bg-indigo-50/30'
          : 'bg-slate-50/60'
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      {isWinner && (
        <span className="absolute top-2.5 right-3">
          {BEST_BADGE}
        </span>
      )}
      {children}
    </div>
  )
}

function RowLabel({ label, hint, tip }) {
  return (
    <div className="flex items-center pl-1">
      <div>
        <p className="text-sm font-semibold text-slate-700 inline-flex items-center">
          {label}
          {tip && <InfoTip label={`About ${label}`}>{tip}</InfoTip>}
        </p>
        {hint && <p className="text-[11px] text-slate-400 mt-1">{hint}</p>}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────

export default function MetricsGrid({ products, yourAsin }) {
  if (!products?.length) return null

  const ordered = [
    ...products.filter(p => p.asin === yourAsin),
    ...products.filter(p => p.asin !== yourAsin),
  ]

  const prices = ordered.map(p => parsePrice(p.price))
  const ratings = ordered.map(p => p.star_rating ?? null)
  const reviewCounts = ordered.map(p => p.total_reviews ?? null)

  const priceWinner = bestIndex(prices, 'min')
  const ratingWinner = bestIndex(ratings, 'max')
  const reviewsWinner = bestIndex(reviewCounts, 'max')

  const productColCount = ordered.length
  const labelCol = '180px'
  const minColWidth = '220px'
  const gridTemplate = `${labelCol} repeat(${productColCount}, minmax(${minColWidth}, 1fr))`

  return (
    <section>
      <div className="flex items-baseline justify-between mb-5 sm:mb-6 gap-3 flex-wrap">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold mb-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
            Comparison
          </p>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Head-to-head metrics
          </h2>
        </div>
        <span className="text-xs text-slate-400 tabular-nums">
          {productColCount} product{productColCount === 1 ? '' : 's'}
        </span>
      </div>

      {/* ── Mobile / sm: product cards stacked vertically ───────── */}
      <div className="md:hidden space-y-4">
        {ordered.map((p, i) => (
          <MobileProductCard
            key={p.asin}
            product={p}
            isYours={p.asin === yourAsin}
            index={i}
            delay={i * 60}
            priceWin={priceWinner === i}
            ratingWin={ratingWinner === i}
            reviewsWin={reviewsWinner === i}
            prices={prices}
            ratings={ratings}
            reviewCounts={reviewCounts}
          />
        ))}
      </div>

      {/* ── md+: comparison table ───────────────────────────────── */}
      <div className="hidden md:block">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 lg:p-7 overflow-x-auto scrollbar-thin">
          <div
            className="grid gap-4 sm:gap-5 items-stretch min-w-[720px]"
            style={{ gridTemplateColumns: gridTemplate }}
          >
            {/* Header row */}
            <div className="flex items-end pb-2">
              <span className="text-[11px] uppercase tracking-[0.18em] text-slate-400 font-semibold">
                Metric
              </span>
            </div>
            {ordered.map((p, i) => (
              <ProductHeaderCell
                key={p.asin}
                product={p}
                isYours={p.asin === yourAsin}
                delay={i * 50}
              />
            ))}

            {/* Price row */}
            <RowLabel label="Price" hint="Lower is better" />
            {ordered.map((p, i) => (
              <MetricCell
                key={`price-${p.asin}`}
                isWinner={priceWinner === i}
                isYours={p.asin === yourAsin}
                delay={120 + i * 50}
              >
                <PriceValue
                  value={p.price}
                  fraction={relativeFraction(prices[i], prices, 'min')}
                  isWinner={priceWinner === i}
                />
              </MetricCell>
            ))}

            {/* Rating row */}
            <RowLabel label="Rating" hint="Higher is better" />
            {ordered.map((p, i) => (
              <MetricCell
                key={`rating-${p.asin}`}
                isWinner={ratingWinner === i}
                isYours={p.asin === yourAsin}
                delay={180 + i * 50}
              >
                <Stars
                  rating={ratings[i]}
                  fraction={ratings[i] != null ? ratings[i] / 5 : 0}
                  tone={ratingWinner === i ? 'emerald' : 'amber'}
                />
              </MetricCell>
            ))}

            {/* Reviews row */}
            <RowLabel label="Total reviews" hint="More = stronger social proof" />
            {ordered.map((p, i) => (
              <MetricCell
                key={`reviews-${p.asin}`}
                isWinner={reviewsWinner === i}
                isYours={p.asin === yourAsin}
                delay={240 + i * 50}
              >
                <ReviewsValue
                  value={reviewCounts[i]}
                  fraction={relativeFraction(reviewCounts[i], reviewCounts, 'max')}
                  isWinner={reviewsWinner === i}
                />
              </MetricCell>
            ))}

            {/* BSR row */}
            <RowLabel
              label="BSR"
              hint="Best Sellers Rank — only meaningful within the same category"
            />
            {ordered.map((p, i) => (
              <MetricCell
                key={`bsr-${p.asin}`}
                isWinner={false}
                isYours={p.asin === yourAsin}
                delay={300 + i * 50}
              >
                <BsrValue value={p.bsr} />
              </MetricCell>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
