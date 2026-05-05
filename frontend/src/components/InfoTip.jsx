/**
 * Tiny accessible help tooltip — pure CSS, no library.
 * Appears on hover OR keyboard focus (and on tap, since tap focuses).
 * Uses a *named group* (`group/tip`) so it doesn't conflict with parent
 * Tailwind groups in the component tree.
 *
 * Usage:
 *   <span>Reviews delta <InfoTip>Difference vs the average competitor</InfoTip></span>
 */

export default function InfoTip({ children, label = 'More info', placement = 'top' }) {
  const placementClass =
    placement === 'bottom'
      ? 'top-full mt-2'
      : 'bottom-full mb-2'
  const arrowClass =
    placement === 'bottom'
      ? 'bottom-full left-1/2 -translate-x-1/2 -mb-1'
      : 'top-full left-1/2 -translate-x-1/2 -mt-1'

  return (
    <span className="relative inline-flex items-center group/tip align-middle">
      <button
        type="button"
        aria-label={label}
        className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-slate-200/80 text-slate-500 text-[9px] font-bold leading-none hover:bg-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:ring-offset-1 transition-colors cursor-help"
      >
        ?
      </button>
      <span
        role="tooltip"
        className={`pointer-events-none absolute left-1/2 -translate-x-1/2 ${placementClass} w-56 px-3 py-2 rounded-lg bg-slate-900 text-white text-[11px] font-normal leading-snug normal-case tracking-normal opacity-0 group-hover/tip:opacity-100 group-focus-within/tip:opacity-100 transition-opacity duration-150 shadow-lg z-50`}
      >
        {children}
        <span
          className={`absolute ${arrowClass} w-2 h-2 bg-slate-900 rotate-45`}
          aria-hidden="true"
        />
      </span>
    </span>
  )
}
