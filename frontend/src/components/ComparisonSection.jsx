/**
 * Positioning panel — explains *why* you're ranked where you're ranked.
 *
 * - Ranking podium at the top (numbered, your row highlighted)
 * - Two-column "Your edge" vs "Competitor edge"
 * - Market gaps as a callout
 */

function RankingPodium({ ranking, yourAsin }) {
  if (!ranking?.length) return null

  return (
    <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-5">
      <div className="flex items-baseline justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">
          Overall ranking
        </h3>
        <span className="text-xs text-slate-400">{ranking.length} ranked</span>
      </div>

      <ol className="space-y-2">
        {ranking.map((item, i) => {
          const isYours = item.toUpperCase().includes(yourAsin.toUpperCase())
          const medalColor =
            i === 0
              ? 'bg-amber-100 text-amber-700 ring-amber-200'
              : i === 1
              ? 'bg-slate-200 text-slate-700 ring-slate-300'
              : i === 2
              ? 'bg-orange-100 text-orange-700 ring-orange-200'
              : 'bg-slate-100 text-slate-500 ring-slate-200'

          return (
            <li
              key={i}
              className={`flex items-start gap-3 p-3 rounded-xl transition animate-fade-up ${
                isYours
                  ? 'bg-indigo-50/60 ring-1 ring-indigo-200'
                  : 'bg-white ring-1 ring-slate-100 hover:ring-slate-200'
              }`}
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <span
                className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold tabular-nums ring-1 ${medalColor}`}
              >
                {i + 1}
              </span>
              <p
                className={`text-sm leading-snug pt-1 ${
                  isYours ? 'text-indigo-900 font-medium' : 'text-slate-700'
                }`}
              >
                {item}
                {isYours && (
                  <span className="ml-2 inline-flex items-center bg-indigo-100 text-indigo-700 text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded">
                    You
                  </span>
                )}
              </p>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

function EdgePanel({ title, items, tone, icon, emptyText }) {
  const tones = {
    indigo: {
      ring: 'ring-indigo-100',
      border: 'border-indigo-200',
      bg: 'bg-gradient-to-br from-indigo-50/50 to-white',
      heading: 'text-indigo-800',
      bullet: 'bg-indigo-400',
      badge: 'bg-indigo-100 text-indigo-700',
    },
    rose: {
      ring: 'ring-rose-100',
      border: 'border-rose-200',
      bg: 'bg-gradient-to-br from-rose-50/40 to-white',
      heading: 'text-rose-800',
      bullet: 'bg-rose-400',
      badge: 'bg-rose-100 text-rose-700',
    },
    amber: {
      ring: 'ring-amber-100',
      border: 'border-amber-200',
      bg: 'bg-gradient-to-br from-amber-50/40 to-white',
      heading: 'text-amber-800',
      bullet: 'bg-amber-400',
      badge: 'bg-amber-100 text-amber-700',
    },
  }
  const t = tones[tone] ?? tones.indigo

  return (
    <div className={`rounded-2xl border ${t.border} ring-1 ${t.ring} ${t.bg} p-5`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className={`font-semibold text-sm flex items-center gap-2 ${t.heading}`}>
          {icon}
          {title}
        </h3>
        <span className={`text-[11px] font-bold tabular-nums px-2 py-0.5 rounded-full ${t.badge}`}>
          {items?.length ?? 0}
        </span>
      </div>
      {items?.length ? (
        <ul className="space-y-2.5">
          {items.map((item, i) => (
            <li
              key={i}
              className="flex gap-2.5 text-sm text-slate-700 leading-relaxed animate-fade-up"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <span className={`flex-shrink-0 mt-1.5 w-1.5 h-1.5 rounded-full ${t.bullet}`} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-slate-400 text-sm">{emptyText}</p>
      )}
    </div>
  )
}

const ICON_TROPHY = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0" />
  </svg>
)

const ICON_TARGET = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
  </svg>
)

const ICON_GAP = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
  </svg>
)

export default function ComparisonSection({ comparison, yourAsin }) {
  const competitorAdvantages = (comparison.competitor_advantages ?? []).flatMap(c =>
    (c.advantages ?? []).map(a => ({
      text: a,
      from: c.product_title || c.asin,
      asin: c.asin,
    })),
  )

  return (
    <section className="space-y-5 sm:space-y-6">
      <div>
        <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold mb-2 flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
          Positioning
        </p>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Where you stand in the field
        </h2>
      </div>

      <div className="grid gap-4 sm:gap-5 lg:grid-cols-3">
        {/* Ranking takes the full left column on lg */}
        <div className="lg:col-span-1">
          <RankingPodium ranking={comparison.overall_ranking ?? []} yourAsin={yourAsin} />
        </div>

        {/* Edge panels stack on the right */}
        <div className="lg:col-span-2 grid gap-4 sm:grid-cols-2">
          <EdgePanel
            title="Your edge"
            items={comparison.your_product_advantages ?? []}
            tone="indigo"
            icon={ICON_TROPHY}
            emptyText="No standout edges identified."
          />
          <div className="rounded-2xl border border-rose-200 ring-1 ring-rose-100 bg-gradient-to-br from-rose-50/40 to-white p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm flex items-center gap-2 text-rose-800">
                {ICON_TARGET}
                Where competitors win
              </h3>
              <span className="text-[11px] font-bold tabular-nums px-2 py-0.5 rounded-full bg-rose-100 text-rose-700">
                {competitorAdvantages.length}
              </span>
            </div>
            {competitorAdvantages.length ? (
              <ul className="space-y-2.5">
                {competitorAdvantages.map((c, i) => (
                  <li
                    key={i}
                    className="text-sm text-slate-700 leading-relaxed flex gap-2.5 animate-fade-up"
                    style={{ animationDelay: `${i * 40}ms` }}
                  >
                    <span className="flex-shrink-0 mt-1.5 w-1.5 h-1.5 rounded-full bg-rose-400" />
                    <span className="flex-1">
                      {c.text}
                      <span className="ml-1.5 text-[11px] text-slate-400 font-mono">
                        {c.asin}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-400 text-sm">No competitor advantages identified.</p>
            )}
          </div>

          <div className="sm:col-span-2">
            <EdgePanel
              title="Market gaps to exploit"
              items={comparison.market_gaps ?? []}
              tone="amber"
              icon={ICON_GAP}
              emptyText="No clear market gaps identified."
            />
          </div>
        </div>
      </div>
    </section>
  )
}
