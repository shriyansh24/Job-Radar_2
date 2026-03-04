import { cn } from '../../lib/utils'

interface StatCardProps {
  label: string
  value: string | number
  color?: string
  subtitle?: string
}

export function StatCard({ label, value, color = 'text-text-primary', subtitle }: StatCardProps) {
  return (
    <div className="bg-surface border border-border rounded-xl p-5">
      <div className="text-xs text-text-secondary mb-2">{label}</div>
      <div className={cn('text-2xl font-mono font-bold', color)}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      {subtitle && (
        <div className="text-xs text-text-secondary mt-1">{subtitle}</div>
      )}
    </div>
  )
}
