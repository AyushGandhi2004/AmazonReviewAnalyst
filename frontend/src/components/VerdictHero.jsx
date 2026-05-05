import ProductImage from './ProductImage'
import InfoTip from './InfoTip'

/**
 * Editorial verdict — oversized rank numeral, headline, an inline stat strip,
 * and a full-width head-to-head section underneath with side-by-side product
 * cards.
 *
 * Read-time goal: 30 seconds to know rank, wins, urgent fixes.
 */

const ORDINAL = ['1st', '2nd', '3rd', '4th', '5th']

function parsePrice(raw) {
  if (!raw) return null
  const num = parseFloat(String(raw).replace(/[^0-9.]/g, ''))
  return Number.isFinite(num) ? num : null
}

// Resolve the rank for a given product from `section_3.comparison.overall_ranking`.
//
// The LLM emits free-text sentences like "The OnePlus Nord Buds 3r is ranked 1
// due to ..." which usually do NOT contain the ASIN. We try, in order:
//   1. ASIN substring   (most reliable when present)
//   2. Model Name       (very distinctive, e.g. "Nirvana ION")
//   3. Model Number     (only if length > 2 to avoid spurious hits)
//   4. Brand + a model token  (e.g. "oneplus" + "nord")
//   5. Brand alone      (works when each brand is unique to one product)
//
// Once a sentence matches, we look for an explicit rank inside the sentence
// ("ranked 2", "#3", "1st place"); if none is found we fall back to the
// position of the sentence in the array (index + 1).
function extractExplicitRank(sentence) {
  const lower = sentence.toLowerCase()
  const patterns = [
    /\branked\s*#?\s*(\d+)\b/,
    /\brank\s*#?\s*(\d+)\b/,
    /#\s*(\d+)\b/,
    /\b(\d+)(?:st|nd|rd|th)\b/,
  ]
  for (const pat of patterns) {
    const m = lower.match(pat)
    if (m) {
      const num = parseInt(m[1], 10)
      if (Number.isFinite(num) && num > 0 && num < 100) return num
    }
  }
  return null
}

function sentenceMatchesProduct(sentence, product, asin) {
  const lower = sentence.toLowerCase()
  if (asin && lower.includes(asin.toLowerCase())) return true
  if (!product) return false

  const specs = product.specifications ?? {}
  const brand = (specs['Brand Name'] ?? '').toLowerCase().trim()
  const modelName = (specs['Model Name'] ?? '').toLowerCase().trim()
  const modelNumber = (specs['Model Number'] ?? '').toLowerCase().trim()

  if (modelName && lower.includes(modelName)) return true
  if (modelNumber && modelNumber.length > 2 && lower.includes(modelNumber)) return true
  if (brand && modelName) {
    const modelToken = modelName.split(/\s+/).find(t => t.length > 2)
    if (modelToken && lower.includes(brand) && lower.includes(modelToken)) return true
  }
  if (brand && brand.length > 2 && lower.includes(brand)) return true

  // Fallback: match against the product title (first two words are usually brand + sub-brand)
  const title = (product.title ?? '').toLowerCase().trim()
  if (title) {
    const words = title.split(/\s+/)
    if (words.length >= 2) {
      const brandPhrase = words.slice(0, 2).join(' ')
      if (brandPhrase.length > 4 && lower.includes(brandPhrase)) return true
    }
    if (words[0] && words[0].length > 3 && lower.includes(words[0])) return true
  }

  return false
}

function findRank(ranking, product, asin) {
  if (!ranking?.length) return null
  for (let i = 0; i < ranking.length; i++) {
    if (sentenceMatchesProduct(ranking[i], product, asin)) {
      return extractExplicitRank(ranking[i]) ?? i + 1
    }
  }
  return null
}

function diffWinsAgainst(you, them) {
  const wins = []
  const losses = []

  const yourPrice = parsePrice(you?.price)
  const theirPrice = parsePrice(them?.price)
  if (yourPrice != null && theirPrice != null && yourPrice !== theirPrice) {
    const pct = Math.round(((theirPrice - yourPrice) / theirPrice) * 100)
    if (yourPrice < theirPrice) wins.push({ metric: 'Price', detail: `${Math.abs(pct)}% cheaper` })
    else losses.push({ metric: 'Price', detail: `${Math.abs(pct)}% pricier` })
  }

  if (you?.star_rating != null && them?.star_rating != null) {
    const d = +(you.star_rating - them.star_rating).toFixed(1)
    if (d > 0) wins.push({ metric: 'Rating', detail: `+${d.toFixed(1)}★` })
    else if (d < 0) losses.push({ metric: 'Rating', detail: `${d.toFixed(1)}★` })
  }

  if (you?.total_reviews != null && them?.total_reviews != null && them.total_reviews > 0) {
    const ratio = you.total_reviews / them.total_reviews
    if (ratio >= 1.15) wins.push({ metric: 'Reviews', detail: `${ratio.toFixed(1)}× more` })
    else if (ratio <= 0.87) losses.push({ metric: 'Reviews', detail: `${(1 / ratio).toFixed(1)}× fewer` })
  }

  return { wins, losses }
}

// ─────────────────────────────────────────────────────────
// Inline stat — used inside the editorial stat strip
// ─────────────────────────────────────────────────────────

function Stat({ label, value, sub, accent = 'slate', tip }) {
  const accents = {
    indigo: 'text-indigo-600',
    emerald: 'text-emerald-600',
    rose: 'text-rose-600',
    amber: 'text-amber-600',
    slate: 'text-slate-900',
  }
  return (
    <div className="flex flex-col gap-1.5 min-w-0">
      <span className="inline-flex items-center text-[10px] uppercase tracking-[0.14em] text-slate-400 font-semibold">
        {label}
        {tip && <InfoTip label={`About ${label}`}>{tip}</InfoTip>}
      </span>
      <span className={`text-2xl sm:text-[28px] font-semibold tabular-nums leading-none tracking-tight ${accents[accent]}`}>
        {value}
      </span>
      {sub && <span className="text-xs text-slate-500 leading-snug">{sub}</span>}
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// Head-to-head card — one per competitor, full-width row
// ─────────────────────────────────────────────────────────

function MetricLine({ youValue, themValue, label, youWin, themWin }) {
  return (
    <>
      <span
        className={`text-right tabular-nums text-sm sm:text-base ${
          youWin ? 'text-emerald-700 font-semibold' : 'text-slate-700'
        }`}
      >
        {youValue ?? <span className="text-slate-300">—</span>}
      </span>
      <span className="text-[10px] uppercase tracking-[0.14em] text-slate-400 font-semibold self-center text-center px-2">
        {label}
      </span>
      <span
        className={`text-left tabular-nums text-sm sm:text-base ${
          themWin ? 'text-emerald-700 font-semibold' : 'text-slate-700'
        }`}
      >
        {themValue ?? <span className="text-slate-300">—</span>}
      </span>
    </>
  )
}

function HeadToHeadCard({ you, them, vs, delay }) {
  const score = vs.wins.length - vs.losses.length
  const scoreText = `${vs.wins.length}–${vs.losses.length}`
  const tone =
    score > 0
      ? { dot: 'bg-emerald-500', label: `You lead ${scoreText}`, ring: 'ring-emerald-200', chipBg: 'bg-emerald-50', chipText: 'text-emerald-700' }
      : score < 0
      ? { dot: 'bg-rose-500', label: `They lead ${scoreText}`, ring: 'ring-rose-200', chipBg: 'bg-rose-50', chipText: 'text-rose-700' }
      : { dot: 'bg-slate-400', label: `Even ${scoreText}`, ring: 'ring-slate-200', chipBg: 'bg-slate-100', chipText: 'text-slate-600' }

  const youPriceWin = vs.wins.some(w => w.metric === 'Price')
  const themPriceWin = vs.losses.some(l => l.metric === 'Price')
  const youRatingWin = vs.wins.some(w => w.metric === 'Rating')
  const themRatingWin = vs.losses.some(l => l.metric === 'Rating')
  const youReviewsWin = vs.wins.some(w => w.metric === 'Reviews')
  const themReviewsWin = vs.losses.some(l => l.metric === 'Reviews')

  return (
    <article
      className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-7 animate-fade-up transition hover:border-slate-300"
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Header */}
      <header className="flex items-center justify-between gap-3 mb-5 sm:mb-6">
        <span className="text-[10px] uppercase tracking-[0.18em] text-slate-400 font-semibold">
          Head-to-head
        </span>
        <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full ${tone.chipBg} ${tone.chipText} ring-1 ${tone.ring}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${tone.dot}`} />
          {tone.label}
        </span>
      </header>

      {/* Side-by-side products */}
      <div className="grid grid-cols-[1fr_auto_1fr] gap-3 sm:gap-5 items-center">
        {/* You */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2.5 sm:gap-3 min-w-0">
          <ProductImage src={you.image_url} alt={you.title} size="lg" />
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-[0.14em] text-indigo-700 font-semibold mb-1">You</p>
            <p className="text-sm font-semibold text-slate-900 leading-snug line-clamp-2">
              {you.title || you.asin}
            </p>
            <p className="font-mono text-[10px] text-slate-400 mt-0.5">{you.asin}</p>
          </div>
        </div>

        {/* vs divider */}
        <div className="flex flex-col items-center gap-1 px-1 sm:px-2 self-stretch justify-center">
          <span className="text-[10px] tracking-[0.14em] uppercase text-slate-300 font-semibold">vs</span>
          <span className="hidden sm:block w-px h-12 bg-slate-200" />
        </div>

        {/* Them */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2.5 sm:gap-3 min-w-0">
          <ProductImage src={them.image_url} alt={them.title} size="lg" />
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-1">Them</p>
            <p className="text-sm font-semibold text-slate-900 leading-snug line-clamp-2">
              {them.title || them.asin}
            </p>
            <p className="font-mono text-[10px] text-slate-400 mt-0.5">{them.asin}</p>
          </div>
        </div>
      </div>

      {/* Aligned metric rows */}
      <dl className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-[1fr_auto_1fr] gap-y-3 gap-x-3 sm:gap-x-5">
        <MetricLine
          youValue={you.price}
          themValue={them.price}
          label="Price"
          youWin={youPriceWin}
          themWin={themPriceWin}
        />
        <MetricLine
          youValue={you.star_rating != null ? `${you.star_rating.toFixed(1)} ★` : null}
          themValue={them.star_rating != null ? `${them.star_rating.toFixed(1)} ★` : null}
          label="Rating"
          youWin={youRatingWin}
          themWin={themRatingWin}
        />
        <MetricLine
          youValue={you.total_reviews?.toLocaleString()}
          themValue={them.total_reviews?.toLocaleString()}
          label="Reviews"
          youWin={youReviewsWin}
          themWin={themReviewsWin}
        />
      </dl>
    </article>
  )
}

// ─────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────

export default function VerdictHero({ report }) {
  const yourAsin = report.your_asin
  const products = report.section_1?.products ?? []
  const yourProduct = products.find(p => p.asin === yourAsin)
  const competitors = products.filter(p => p.asin !== yourAsin)

  const ranking = report.section_3?.comparison?.overall_ranking ?? []
  const rank = findRank(ranking, yourProduct, yourAsin)
  const totalRanked = ranking.length || products.length

  const recommendations = report.section_4?.recommendations?.recommendations ?? []
  const highPriority = recommendations.filter(r => r.priority === 'high')

  const vsList = competitors.map(c => ({
    competitor: c,
    vs: yourProduct ? diffWinsAgainst(yourProduct, c) : { wins: [], losses: [] },
  }))

  const totalWins = vsList.reduce((acc, v) => acc + v.vs.wins.length, 0)
  const totalLosses = vsList.reduce((acc, v) => acc + v.vs.losses.length, 0)
  const competitorsBeaten = vsList.filter(v => v.vs.wins.length > v.vs.losses.length).length

  const avgCompReviews = competitors.length
    ? Math.round(competitors.reduce((acc, c) => acc + (c.total_reviews || 0), 0) / competitors.length)
    : 0
  const reviewsDelta = yourProduct?.total_reviews != null && avgCompReviews
    ? yourProduct.total_reviews - avgCompReviews
    : null

  const headline = (() => {
    if (rank === 1) return "You're leading the field."
    if (rank && rank <= Math.ceil(totalRanked / 2) && competitorsBeaten >= competitors.length / 2)
      return "You're holding strong — with a few clear gaps to close."
    if (highPriority.length >= 3) return "You have ground to make up — but the path is clear."
    if (competitors.length === 0) return "Here's how your product is performing."
    return "You're competitive — with sharp moves, you can pull ahead."
  })()

  const subline = (() => {
    if (rank === 1) return `Out of ${totalRanked} products analyzed, yours leads on overall positioning. Hold the lead by acting on the priorities below.`
    if (competitors.length === 0) return 'No competitors selected for this run.'
    return `You ${competitorsBeaten === 1 ? 'lead' : 'lead'} ${competitorsBeaten} of ${competitors.length} competitor${competitors.length > 1 ? 's' : ''} head-to-head, with ${highPriority.length} urgent fix${highPriority.length === 1 ? '' : 'es'} flagged.`
  })()

  const rankAccent = rank === 1 ? 'emerald' : rank && rank <= 2 ? 'indigo' : 'amber'
  const rankColor = {
    emerald: 'text-emerald-600',
    indigo: 'text-indigo-600',
    amber: 'text-amber-600',
  }[rankAccent]

  return (
    <section className="space-y-10 sm:space-y-12">
      {/* ── Editorial header ─────────────────────────────────────── */}
      <div className="grid gap-6 sm:gap-8 lg:gap-12 lg:grid-cols-12 items-start">
        {/* Rank numeral */}
        <div className="lg:col-span-4 animate-fade-up">
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold mb-3 sm:mb-5 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse-soft" />
            Verdict
          </p>
          <div className="flex items-baseline gap-3">
            <span
              className={`text-[88px] sm:text-[120px] lg:text-[140px] font-light leading-[0.9] tabular-nums tracking-tight ${rankColor}`}
            >
              {rank ? String(rank).padStart(2, '0') : '—'}
            </span>
            <span className="text-sm sm:text-base text-slate-400 pb-2">
              of {totalRanked}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2 sm:mt-3">
            {rank ? `Ranked ${ORDINAL[rank - 1] ?? `${rank}th`} overall` : 'Ranking unavailable'}
          </p>
        </div>

        {/* Headline + stats */}
        <div className="lg:col-span-8 space-y-6 sm:space-y-8 animate-fade-up" style={{ animationDelay: '60ms' }}>
          <div>
            <h2 className="text-3xl sm:text-4xl lg:text-[44px] font-bold text-slate-900 tracking-tight leading-[1.1] text-balance">
              {headline}
            </h2>
            <p className="text-slate-500 text-sm sm:text-base leading-relaxed mt-3 sm:mt-4 max-w-2xl">
              {subline}
            </p>
          </div>

          {/* Inline stat strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 sm:gap-x-8 gap-y-6 pt-6 sm:pt-7 border-t border-slate-200">
            <Stat
              label="Wins"
              value={totalWins}
              sub={competitors.length ? `Across ${competitors.length} rival${competitors.length === 1 ? '' : 's'}` : '—'}
              accent="emerald"
              tip="Concrete head-to-head wins (price, rating, or review count) summed across every competitor."
            />
            <Stat
              label="They win"
              value={totalLosses}
              sub={highPriority.length ? `${highPriority.length} urgent fix${highPriority.length === 1 ? '' : 'es'}` : 'Nothing urgent'}
              accent={totalLosses > totalWins ? 'rose' : 'slate'}
              tip="Metrics where every competitor outperforms you, summed across the field."
            />
            <Stat
              label="Beaten"
              value={`${competitorsBeaten}/${competitors.length || 0}`}
              sub="Competitors you outperform"
              accent={competitorsBeaten === competitors.length && competitors.length > 0 ? 'emerald' : 'slate'}
              tip="A competitor counts as 'beaten' when you win on more metrics than they do head-to-head."
            />
            <Stat
              label="Reviews delta"
              value={
                reviewsDelta == null
                  ? '—'
                  : `${reviewsDelta > 0 ? '+' : ''}${Math.abs(reviewsDelta) >= 1000 ? `${(reviewsDelta / 1000).toFixed(1)}K` : reviewsDelta.toLocaleString()}`
              }
              sub={reviewsDelta == null ? 'Not enough data' : 'vs competitor average'}
              accent={reviewsDelta == null ? 'slate' : reviewsDelta >= 0 ? 'emerald' : 'rose'}
              tip="Difference between your total review count and the average review count of the competitors selected. Positive means more social proof; negative means less."
            />
          </div>
        </div>
      </div>

      {/* ── Head-to-head full-width section ──────────────────────── */}
      {competitors.length > 0 && yourProduct && (
        <div>
          <div className="flex items-baseline justify-between mb-5 sm:mb-6">
            <h3 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
              Head-to-head
            </h3>
            <span className="text-xs text-slate-400 tabular-nums">
              {competitors.length} matchup{competitors.length === 1 ? '' : 's'}
            </span>
          </div>
          <div className="space-y-4 sm:space-y-5">
            {vsList.map(({ competitor, vs }, i) => (
              <HeadToHeadCard
                key={competitor.asin}
                you={yourProduct}
                them={competitor}
                vs={vs}
                delay={140 + i * 80}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
