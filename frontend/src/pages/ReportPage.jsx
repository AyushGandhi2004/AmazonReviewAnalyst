import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { openProgressStream, fetchReport, pdfUrl } from '../api/client'
import { sampleReport } from '../data/sampleReport'
import ProgressTracker from '../components/ProgressTracker'
import VerdictHero from '../components/VerdictHero'
import TopActions from '../components/TopActions'
import MetricsGrid from '../components/MetricsGrid'
import SpecComparison from '../components/SpecComparison'
import ProductSummaryCard from '../components/ProductSummaryCard'
import ComparisonSection from '../components/ComparisonSection'
import RecommendationCard from '../components/RecommendationCard'
import ReviewSamplesSection from '../components/ReviewSamplesSection'

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 }

const SECTIONS = [
  { id: 'verdict', label: 'Verdict' },
  { id: 'metrics', label: 'Metrics' },
  { id: 'specs', label: 'Specs' },
  { id: 'narrative', label: 'Strengths' },
  { id: 'positioning', label: 'Positioning' },
  { id: 'action-plan', label: 'Action plan' },
  { id: 'reviews', label: 'Reviews' },
]

const LENS_TABS = [
  { id: 'strengths', label: 'Strengths' },
  { id: 'weaknesses', label: 'Weaknesses' },
  { id: 'top_praises', label: 'What they love' },
  { id: 'top_complaints', label: 'What they dislike' },
]

// ─────────────────────────────────────────────────────────
// Header
// ─────────────────────────────────────────────────────────

function Header({ runId, phase, scrolled, preview }) {
  return (
    <header
      className={`sticky top-0 z-30 transition-all duration-200 ${
        scrolled
          ? 'bg-white/85 backdrop-blur-md border-b border-slate-200'
          : 'bg-white border-b border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 px-4 sm:px-6 py-3.5">
        <div className="flex items-center gap-3 min-w-0">
          <Link
            to="/"
            className="text-indigo-600 font-bold text-xl tracking-tight hover:text-indigo-700 transition flex-shrink-0"
          >
            ReviewAnalyst
          </Link>
          {preview && (
            <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-700 ring-1 ring-amber-200 rounded-full px-2.5 py-0.5 text-[11px] font-semibold">
              <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse-soft" />
              Preview · sample data
            </span>
          )}
        </div>

        {phase === 'done' && (
          <div className="flex items-center gap-2">
            <Link
              to="/"
              className="hidden sm:inline-flex items-center gap-1.5 text-slate-600 hover:text-slate-900 font-medium text-sm px-3 py-2 rounded-xl transition"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              New analysis
            </Link>
            {!preview && (
              <a
                href={pdfUrl(runId)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-xl px-3.5 py-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
                Download PDF
              </a>
            )}
          </div>
        )}
      </div>
    </header>
  )
}

// ─────────────────────────────────────────────────────────
// Section anchor nav (scroll-spy)
// ─────────────────────────────────────────────────────────

function SectionNav({ activeSection, onJump }) {
  return (
    <nav className="sticky top-[57px] z-20 bg-slate-50/85 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-thin py-2.5">
          {SECTIONS.map(s => {
            const isActive = activeSection === s.id
            return (
              <button
                key={s.id}
                onClick={() => onJump(s.id)}
                className={`relative px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition ${
                  isActive
                    ? 'text-slate-900 bg-white ring-1 ring-slate-200 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {s.label}
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}

// ─────────────────────────────────────────────────────────
// Strengths / Weaknesses tabbed comparison
// ─────────────────────────────────────────────────────────

function StrengthsCompare({ summaries, yourAsin, imagesByAsin = {} }) {
  const [lens, setLens] = useState('strengths')

  const ordered = useMemo(() => {
    if (!summaries?.length) return []
    return [
      ...summaries.filter(s => s.asin === yourAsin),
      ...summaries.filter(s => s.asin !== yourAsin),
    ]
  }, [summaries, yourAsin])

  // Counts per tab — useful preview on the tab itself
  const counts = useMemo(() => {
    const c = { strengths: 0, weaknesses: 0, top_praises: 0, top_complaints: 0 }
    summaries?.forEach(s => {
      Object.keys(c).forEach(k => {
        c[k] += (s[k]?.length ?? 0)
      })
    })
    return c
  }, [summaries])

  if (!ordered.length) return null

  const cols =
    ordered.length === 1
      ? 'grid-cols-1'
      : ordered.length === 2
      ? 'grid-cols-1 md:grid-cols-2'
      : ordered.length === 3
      ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
      : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'

  return (
    <section>
      <div className="flex items-baseline justify-between mb-5 sm:mb-6 gap-3 flex-wrap">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold mb-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
            Narrative
          </p>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Side-by-side themes
          </h2>
        </div>
        <span className="text-xs text-slate-400 tabular-nums">{ordered.length} products</span>
      </div>

      {/* Tab bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-1 mb-6 sm:mb-8 inline-flex flex-wrap gap-1 max-w-full">
        {LENS_TABS.map(t => {
          const isActive = lens === t.id
          return (
            <button
              key={t.id}
              onClick={() => setLens(t.id)}
              className={`relative px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition ${
                isActive
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <span className="flex items-center gap-2">
                {t.label}
                <span
                  className={`tabular-nums text-[10px] px-1.5 py-0.5 rounded-full ${
                    isActive ? 'bg-white/15 text-white/80' : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {counts[t.id]}
                </span>
              </span>
            </button>
          )
        })}
      </div>

      <div className={`grid gap-4 sm:gap-5 ${cols}`}>
        {ordered.map(s => (
          <ProductSummaryCard
            key={s.asin}
            summary={s}
            isYours={s.asin === yourAsin}
            lens={lens}
            imageUrl={imagesByAsin[s.asin]}
          />
        ))}
      </div>
    </section>
  )
}

// ─────────────────────────────────────────────────────────
// Action plan with filter chips + counts
// ─────────────────────────────────────────────────────────

function ActionPlan({ recommendations }) {
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [areaFilter, setAreaFilter] = useState('all')

  const counts = useMemo(() => {
    const byPriority = { high: 0, medium: 0, low: 0 }
    const byArea = { product: 0, listing: 0, pricing: 0 }
    recommendations.forEach(r => {
      if (byPriority[r.priority] != null) byPriority[r.priority]++
      if (byArea[r.area] != null) byArea[r.area]++
    })
    return { byPriority, byArea, total: recommendations.length }
  }, [recommendations])

  const filtered = useMemo(() => {
    return [...recommendations]
      .filter(r => priorityFilter === 'all' || r.priority === priorityFilter)
      .filter(r => areaFilter === 'all' || r.area === areaFilter)
      .sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 3) - (PRIORITY_ORDER[b.priority] ?? 3))
  }, [recommendations, priorityFilter, areaFilter])

  const priorityChips = [
    { id: 'all', label: 'All', dot: 'bg-slate-400', count: counts.total },
    { id: 'high', label: 'High', dot: 'bg-rose-500', count: counts.byPriority.high },
    { id: 'medium', label: 'Medium', dot: 'bg-amber-500', count: counts.byPriority.medium },
    { id: 'low', label: 'Low', dot: 'bg-slate-300', count: counts.byPriority.low },
  ]
  const areaChips = [
    { id: 'all', label: 'All areas' },
    { id: 'product', label: 'Product' },
    { id: 'listing', label: 'Listing' },
    { id: 'pricing', label: 'Pricing' },
  ]

  return (
    <section>
      <div className="flex items-baseline justify-between mb-5 sm:mb-6 flex-wrap gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold mb-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
            Action plan
          </p>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            What to do next, ranked
          </h2>
        </div>
        <span className="text-xs text-slate-400 tabular-nums">
          {filtered.length} of {counts.total} action{counts.total === 1 ? '' : 's'}
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6 sm:mb-8 flex-wrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          {priorityChips.map(chip => {
            const isActive = priorityFilter === chip.id
            return (
              <button
                key={chip.id}
                onClick={() => setPriorityFilter(chip.id)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition ${
                  isActive
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${chip.dot}`} />
                {chip.label}
                <span
                  className={`tabular-nums text-[10px] px-1.5 py-0.5 rounded-full ${
                    isActive ? 'bg-white/15 text-white/80' : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {chip.count}
                </span>
              </button>
            )
          })}
        </div>
        <div className="hidden sm:block w-px h-5 bg-slate-200" />
        <div className="flex items-center gap-1.5 flex-wrap">
          {areaChips.map(chip => {
            const isActive = areaFilter === chip.id
            return (
              <button
                key={chip.id}
                onClick={() => setAreaFilter(chip.id)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                {chip.label}
              </button>
            )
          })}
        </div>
      </div>

      {filtered.length > 0 ? (
        <div className="space-y-2.5">
          {filtered.map((rec, i) => (
            <div
              key={`${rec.action}-${i}`}
              className="animate-fade-up"
              style={{ animationDelay: `${Math.min(i * 30, 250)}ms` }}
            >
              <RecommendationCard recommendation={rec} index={i} />
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-200 p-10 text-center text-slate-400 text-sm">
          No actions match the current filter.
        </div>
      )}
    </section>
  )
}

// ─────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────

export default function ReportPage({ preview = false }) {
  const { runId: paramRunId } = useParams()
  const runId = paramRunId ?? 'preview'
  const [events, setEvents] = useState([])
  const [report, setReport] = useState(preview ? sampleReport : null)
  const [error, setError] = useState('')
  const [phase, setPhase] = useState(preview ? 'done' : 'loading') // loading | done | error
  const [scrolled, setScrolled] = useState(false)
  const [activeSection, setActiveSection] = useState(SECTIONS[0].id)

  // ── SSE connection ─────────────────────────────────────
  const startSSE = useCallback(() => {
    const es = openProgressStream(runId)

    es.addEventListener('progress', e => {
      try {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, data])
        if (data.status === 'error') {
          setError(data.message || 'The analysis pipeline encountered an error.')
          setPhase('error')
          es.close()
        }
      } catch {
        // malformed event — ignore
      }
    })

    es.addEventListener('analysis_done', e => {
      try {
        const data = JSON.parse(e.data)
        setReport(data)
        setPhase('done')
      } catch {
        setError('Failed to parse the analysis report.')
        setPhase('error')
      }
      es.close()
    })

    es.addEventListener('keepalive', () => {})

    es.onerror = () => {
      es.close()
      // The server closes the stream cleanly after analysis_done; treat that
      // close as success rather than as an error.
      setPhase(prev => {
        if (prev === 'done') return prev
        setError('Connection to the server was lost. Please refresh the page.')
        return 'error'
      })
    }

    return es
  }, [runId])

  useEffect(() => {
    if (preview) return // preview mode renders sample data — never hits the API
    let es = null

    fetchReport(runId)
      .then(data => {
        if (data) {
          setReport(data)
          setPhase('done')
        } else {
          es = startSSE()
        }
      })
      .catch(err => {
        if (err.message.includes('404')) {
          setError('Analysis run not found. It may have expired.')
          setPhase('error')
        } else {
          es = startSSE()
        }
      })

    return () => {
      if (es) es.close()
    }
  }, [runId, startSSE, preview])

  // ── Header bg on scroll ────────────────────────────────
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // ── Scroll-spy: track which section is in view ─────────
  useEffect(() => {
    if (phase !== 'done') return

    const observer = new IntersectionObserver(
      entries => {
        // Pick the entry closest to the top of the viewport that is intersecting.
        const visible = entries
          .filter(e => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (visible[0]) setActiveSection(visible[0].target.id)
      },
      {
        rootMargin: '-120px 0px -55% 0px',
        threshold: 0,
      },
    )

    SECTIONS.forEach(s => {
      const el = document.getElementById(s.id)
      if (el) observer.observe(el)
    })

    return () => observer.disconnect()
  }, [phase])

  const handleJump = useCallback(id => {
    const el = document.getElementById(id)
    if (!el) return
    const yOffset = -110 // accounts for sticky header + nav
    const y = el.getBoundingClientRect().top + window.scrollY + yOffset
    window.scrollTo({ top: y, behavior: 'smooth' })
  }, [])

  const recommendations = report?.section_4?.recommendations?.recommendations ?? []

  // Build asin → image_url map so child sections can show product thumbnails
  // without each having to know about section_1's product list.
  const imagesByAsin = useMemo(() => {
    const map = {}
    ;(report?.section_1?.products ?? []).forEach(p => {
      if (p.image_url) map[p.asin] = p.image_url
    })
    return map
  }, [report])

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Header runId={runId} phase={phase} scrolled={scrolled} preview={preview} />

      {phase === 'done' && <SectionNav activeSection={activeSection} onJump={handleJump} />}

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-8 sm:py-10">
        {/* ── Loading ───────────────────────────────────── */}
        {phase === 'loading' && (
          <div className="py-8 animate-fade-in">
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 rounded-full px-3 py-1 text-xs font-semibold mb-4">
                <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse-soft" />
                Working
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-2 tracking-tight">
                Analyzing your products
              </h1>
              <p className="text-slate-500 text-sm">
                This usually takes 2–5 minutes. Don't close this tab.
              </p>
            </div>
            <ProgressTracker events={events} />
          </div>
        )}

        {/* ── Error ─────────────────────────────────────── */}
        {phase === 'error' && (
          <div className="max-w-xl mx-auto py-16 text-center animate-fade-up">
            <div className="bg-white border border-rose-200 rounded-2xl p-8 shadow-sm">
              <div className="w-12 h-12 rounded-full bg-rose-50 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
              </div>
              <p className="text-slate-900 font-semibold text-base mb-2">Analysis failed</p>
              <p className="text-slate-500 text-sm mb-6 leading-relaxed">{error}</p>
              <Link
                to="/"
                className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-xl px-4 py-2 text-sm transition"
              >
                ← Try again
              </Link>
            </div>
          </div>
        )}

        {/* ── Done ──────────────────────────────────────── */}
        {phase === 'done' && report && (
          <div className="space-y-16 sm:space-y-20">
            {/* Run meta strip */}
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 animate-fade-in">
              <span className="inline-flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {new Date(report.created_at).toLocaleString(undefined, {
                  dateStyle: 'medium',
                  timeStyle: 'short',
                })}
              </span>
              <span className="text-slate-300">·</span>
              <span className="font-mono">Run {report.run_id.slice(0, 8)}</span>
            </div>

            {/* 1. Verdict — TL;DR + head-to-head + top actions live together */}
            <div id="verdict" className="scroll-mt-32 space-y-12 sm:space-y-16">
              <VerdictHero report={report} />
              <TopActions recommendations={recommendations} anchor="#action-plan" />
            </div>

            {/* 2. Metrics */}
            <div id="metrics" className="scroll-mt-32">
              <MetricsGrid
                products={report.section_1?.products ?? []}
                yourAsin={report.your_asin}
              />
            </div>

            {/* 3. Spec face-off — only render when the table has rows */}
            {report.section_3?.comparison_table?.length > 0 && (
              <div id="specs" className="scroll-mt-32">
                <SpecComparison
                  table={report.section_3.comparison_table}
                  products={report.section_1?.products ?? []}
                  yourAsin={report.your_asin}
                />
              </div>
            )}

            {/* 4. Narrative comparison */}
            <div id="narrative" className="scroll-mt-32">
              <StrengthsCompare
                summaries={report.section_2?.summaries ?? []}
                yourAsin={report.your_asin}
                imagesByAsin={imagesByAsin}
              />
            </div>

            {/* 4. Positioning */}
            <div id="positioning" className="scroll-mt-32">
              <ComparisonSection
                comparison={report.section_3?.comparison ?? {}}
                yourAsin={report.your_asin}
              />
            </div>

            {/* 5. Action plan */}
            <div id="action-plan" className="scroll-mt-32">
              <ActionPlan recommendations={recommendations} />
            </div>

            {/* 6. Voice of customer */}
            <div id="reviews" className="scroll-mt-32">
              <ReviewSamplesSection
                samples={report.section_5?.samples ?? []}
                yourAsin={report.your_asin}
                imagesByAsin={imagesByAsin}
              />
            </div>

            {/* Footer CTA */}
            <div className="border-t border-slate-200 pt-8 mt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <p className="font-semibold text-slate-800 text-sm">Want to analyze another product?</p>
                <p className="text-slate-500 text-xs mt-0.5">Run a new comparison from the home page.</p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  to="/"
                  className="inline-flex items-center gap-2 border border-slate-200 text-slate-700 hover:bg-white font-medium rounded-xl px-4 py-2 text-sm transition"
                >
                  ← New analysis
                </Link>
                {!preview && (
                  <a
                    href={pdfUrl(runId)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-xl px-4 py-2 text-sm transition"
                  >
                    Download PDF
                  </a>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
