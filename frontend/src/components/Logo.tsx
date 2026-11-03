import { BRAND_GRADIENT_ID } from '../lib/brand'

export const APP_NAME = 'Tasklane'

// Tasklane logo: three rising "lanes" (Kanban columns) on a teal tile.
export default function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" role="img" aria-label={APP_NAME}>
      <defs>
        <linearGradient id={BRAND_GRADIENT_ID} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#0f766e" />
          <stop offset="1" stopColor="#2dd4bf" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill={`url(#${BRAND_GRADIENT_ID})`} />
      <rect x="7" y="8" width="5" height="16" rx="2.5" fill="#fff" />
      <rect x="13.5" y="12" width="5" height="12" rx="2.5" fill="#fff" fillOpacity="0.85" />
      <rect x="20" y="16.5" width="5" height="7.5" rx="2.5" fill="#fff" fillOpacity="0.65" />
    </svg>
  )
}
