import { formatDistanceToNow } from 'date-fns'

export function timeAgo(date: string | Date | null | undefined): string {
  if (!date) return ''
  try {
    return formatDistanceToNow(new Date(date), { addSuffix: true })
  } catch {
    return ''
  }
}

export function formatSalary(min?: number | null, max?: number | null, currency = 'USD'): string {
  if (!min && !max) return ''
  const fmt = (n: number) => {
    if (n >= 1000) return `${Math.round(n / 1000)}k`
    return n.toString()
  }
  if (min && max && min !== max) return `$${fmt(min)} - $${fmt(max)}`
  if (min) return `$${fmt(min)}+`
  if (max) return `Up to $${fmt(max)}`
  return ''
}

export function getInitials(name: string): string {
  return name
    .split(/[\s-]+/)
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ')
}
