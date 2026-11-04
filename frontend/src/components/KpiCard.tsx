import { useRef } from 'react'
import { useCountUp } from '../hooks/useCountUp'
import type { KpiTheme } from '../lib/kpiThemes'

// Compact stat card with a subtle tilt toward the mouse. Pass onClick to make it a button.
export default function KpiCard({
  title,
  value,
  icon,
  theme,
  onClick,
}: {
  title: string
  value: number
  icon: React.ReactNode
  theme: KpiTheme
  onClick?: () => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  const shown = useCountUp(value)

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width - 0.5
    const y = (e.clientY - r.top) / r.height - 0.5
    el.style.setProperty('--rx', `${(-y * 6).toFixed(2)}deg`)
    el.style.setProperty('--ry', `${(x * 8).toFixed(2)}deg`)
  }
  const onLeave = () => {
    ref.current?.style.setProperty('--rx', '0deg')
    ref.current?.style.setProperty('--ry', '0deg')
  }

  return (
    <div
      ref={ref}
      className={`kpi-card${onClick ? ' clickable' : ''}`}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      onClick={onClick}
      {...(onClick
        ? {
            role: 'button',
            tabIndex: 0,
            onKeyDown: (e: React.KeyboardEvent) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onClick()
              }
            },
          }
        : {})}
      style={{ '--from': theme.from, '--to': theme.to } as React.CSSProperties}
    >
      <div className="kpi-top">
        <span className="kpi-title">{title}</span>
        <span className="kpi-icon">{icon}</span>
      </div>
      <div className="kpi-value">{shown}</div>
    </div>
  )
}
