export interface KpiTheme {
  from: string
  to: string
}

// Accent pairs for the KPI cards: teal family first, then supporting colours.
export const KPI_THEMES: KpiTheme[] = [
  { from: '#0d9488', to: '#14b8a6' },
  { from: '#0891b2', to: '#06b6d4' },
  { from: '#059669', to: '#10b981' },
  { from: '#2563eb', to: '#3b82f6' },
  { from: '#e11d48', to: '#f43f5e' },
  { from: '#d97706', to: '#f59e0b' },
]

export const KPI_DANGER = KPI_THEMES[4]
