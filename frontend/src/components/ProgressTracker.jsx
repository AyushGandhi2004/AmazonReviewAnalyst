const MILESTONES = [
  'Input validated',
  'Product data scraped',
  'Reviews collected',
  'Reviews indexed',
  'Review insights extracted',
  'AI analysis complete',
  'Report ready',
]

export default function ProgressTracker({ events }) {
  const latestPct = events.length > 0
    ? Math.max(...events.map(e => e.progress_pct ?? 0))
    : 0

  const doneSet = new Set(
    events.filter(e => e.status === 'done').map(e => e.step),
  )

  const runningEvents = events.filter(e => e.status === 'running')
  const currentRunning = runningEvents.length > 0
    ? runningEvents[runningEvents.length - 1].step
    : null

  const activeIndex = MILESTONES.findIndex(m => !doneSet.has(m))

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 max-w-lg mx-auto animate-fade-up">
      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex justify-between items-baseline mb-2">
          <span className="text-sm font-medium text-slate-600">Analyzing products</span>
          <span className="text-sm font-bold text-indigo-600 tabular-nums">{latestPct}%</span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${latestPct}%` }}
          />
        </div>
        {currentRunning && (
          <p className="text-xs text-slate-500 mt-2.5 flex items-center gap-1.5">
            <span className="relative flex w-1.5 h-1.5">
              <span className="absolute inset-0 bg-indigo-400 rounded-full animate-pulse-soft" />
              <span className="relative bg-indigo-500 rounded-full w-1.5 h-1.5" />
            </span>
            {currentRunning}…
          </p>
        )}
      </div>

      {/* Step list */}
      <ul className="space-y-3.5">
        {MILESTONES.map((milestone, i) => {
          const isDone = doneSet.has(milestone)
          const isActive = i === activeIndex && latestPct > 0

          return (
            <li key={milestone} className="flex items-center gap-3">
              <div
                className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isDone
                    ? 'bg-emerald-100'
                    : isActive
                    ? 'bg-indigo-100 ring-4 ring-indigo-50'
                    : 'bg-slate-100'
                }`}
              >
                {isDone ? (
                  <svg
                    className="w-3.5 h-3.5 text-emerald-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : isActive ? (
                  <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse-soft" />
                ) : (
                  <span className="w-1.5 h-1.5 bg-slate-300 rounded-full" />
                )}
              </div>
              <span
                className={`text-sm transition-colors ${
                  isDone
                    ? 'text-slate-700'
                    : isActive
                    ? 'text-indigo-700 font-medium'
                    : 'text-slate-400'
                }`}
              >
                {milestone}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
