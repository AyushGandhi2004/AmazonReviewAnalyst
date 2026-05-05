import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { startAnalysis } from '../api/client'

const FEATURES = [
  { title: 'Live scraping', desc: 'Real-time Amazon data' },
  { title: 'RAG-powered', desc: 'Review intelligence' },
  { title: 'PDF export', desc: 'Shareable reports' },
]

export default function InputPage() {
  const navigate = useNavigate()
  const [yourAsin, setYourAsin] = useState('')
  const [competitors, setCompetitors] = useState(['', '', ''])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function updateCompetitor(index, value) {
    const next = [...competitors]
    next[index] = value.trim().toUpperCase()
    setCompetitors(next)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { run_id } = await startAnalysis(yourAsin, competitors)
      navigate(`/report/${run_id}`)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <span className="text-indigo-600 font-bold text-xl tracking-tight">ReviewAnalyst</span>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-4 py-12 sm:py-16">
        <div className="w-full max-w-2xl">
          {/* Badge + headline */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 rounded-full px-4 py-1.5 text-sm font-medium mb-5">
              <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
              AI-powered competitive intelligence
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4 leading-tight">
              Understand your Amazon<br className="hidden sm:block" /> competition in minutes
            </h1>
            <p className="text-slate-500 text-base sm:text-lg max-w-lg mx-auto">
              Paste your product ASIN and up to 3 competitors. We'll scrape reviews,
              run AI analysis, and deliver a full competitive report.
            </p>
          </div>

          {/* Form card */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Your product */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                  Your Product ASIN
                  <span className="text-rose-500 ml-0.5">*</span>
                </label>
                <input
                  type="text"
                  value={yourAsin}
                  onChange={e => setYourAsin(e.target.value.trim().toUpperCase())}
                  placeholder="e.g. B08N5WRWNW"
                  required
                  maxLength={10}
                  spellCheck={false}
                  className="w-full border border-slate-300 rounded-xl px-4 py-3 text-slate-900 font-mono placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition text-sm"
                />
                <p className="mt-1 text-xs text-slate-400">10-character Amazon product identifier starting with B or a digit</p>
              </div>

              {/* Competitors */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                  Competitor ASINs
                  <span className="text-slate-400 font-normal ml-1">(optional, up to 3)</span>
                </label>
                <div className="space-y-2.5">
                  {competitors.map((val, i) => (
                    <input
                      key={i}
                      type="text"
                      value={val}
                      onChange={e => updateCompetitor(i, e.target.value)}
                      placeholder={`Competitor ${i + 1} — e.g. B07XK9V1WC`}
                      maxLength={10}
                      spellCheck={false}
                      className="w-full border border-slate-200 rounded-xl px-4 py-3 text-slate-900 font-mono placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition text-sm bg-slate-50"
                    />
                  ))}
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="bg-rose-50 border border-rose-200 rounded-xl px-4 py-3 text-rose-700 text-sm">
                  {error}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={loading || !yourAsin.trim()}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl px-6 py-3.5 transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 flex items-center justify-center gap-2 text-sm"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Starting analysis…
                  </>
                ) : (
                  <>
                    Run Analysis
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Feature pills */}
          <div className="mt-8 grid grid-cols-3 gap-3">
            {FEATURES.map(f => (
              <div key={f.title} className="bg-white rounded-xl border border-slate-200 p-3.5 text-center">
                <p className="font-semibold text-slate-800 text-xs sm:text-sm">{f.title}</p>
                <p className="text-slate-500 text-xs mt-0.5">{f.desc}</p>
              </div>
            ))}
          </div>

          <p className="text-center text-xs text-slate-400 mt-6">
            Analysis takes 2–5 minutes · Supports Amazon.com only
          </p>
        </div>
      </main>
    </div>
  )
}
