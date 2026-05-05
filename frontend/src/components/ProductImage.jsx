import { useState } from 'react'

/**
 * Square product thumbnail with graceful fallback.
 * - If `src` is falsy or fails to load, renders a subtle SVG placeholder.
 * - Always uses `object-cover` so non-square images don't distort.
 *
 * Sizes: sm (40px) · md (56px) · lg (72px) · xl (96px)
 */

const SIZE = {
  sm: 'w-10 h-10',
  md: 'w-14 h-14',
  lg: 'w-[72px] h-[72px]',
  xl: 'w-24 h-24',
}

const RADIUS = {
  sm: 'rounded-md',
  md: 'rounded-lg',
  lg: 'rounded-xl',
  xl: 'rounded-xl',
}

function Placeholder({ sizeClass, radiusClass }) {
  return (
    <div
      className={`${sizeClass} ${radiusClass} bg-slate-100 ring-1 ring-slate-200 flex items-center justify-center text-slate-300 flex-shrink-0`}
      aria-hidden="true"
    >
      <svg className="w-1/2 h-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
      </svg>
    </div>
  )
}

export default function ProductImage({ src, alt = '', size = 'md', className = '' }) {
  const [errored, setErrored] = useState(false)
  const sizeClass = SIZE[size] ?? SIZE.md
  const radiusClass = RADIUS[size] ?? RADIUS.md

  if (!src || errored) {
    return <Placeholder sizeClass={sizeClass} radiusClass={radiusClass} />
  }

  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      decoding="async"
      onError={() => setErrored(true)}
      className={`${sizeClass} ${radiusClass} object-cover bg-slate-50 ring-1 ring-slate-200 flex-shrink-0 ${className}`}
    />
  )
}
