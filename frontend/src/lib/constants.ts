export const SOURCE_COLORS: Record<string, string> = {
  greenhouse: 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10',
  lever: 'text-violet-400 border-violet-400/30 bg-violet-400/10',
  ashby: 'text-orange-400 border-orange-400/30 bg-orange-400/10',
  serpapi: 'text-red-400 border-red-400/30 bg-red-400/10',
  jobspy: 'text-slate-400 border-slate-400/30 bg-slate-400/10',
  theirstack: 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10',
}

export const STATUS_COLORS: Record<string, string> = {
  new: 'text-[#10B981]',
  saved: 'text-[#F5A623]',
  applied: 'text-[#3291FF]',
  interviewing: 'text-purple-400',
  offer: 'text-pink-400',
  rejected: 'text-[#E00000]',
  ghosted: 'text-slate-500',
}

export const STATUS_BG_COLORS: Record<string, string> = {
  new: 'bg-[#10B981]/10',
  saved: 'bg-[#F5A623]/10',
  applied: 'bg-[#3291FF]/10',
  interviewing: 'bg-purple-400/10',
  offer: 'bg-pink-400/10',
  rejected: 'bg-[#E00000]/10',
  ghosted: 'bg-slate-500/10',
}

export const PIPELINE_COLUMNS = [
  'saved',
  'applied',
  'phone_screen',
  'interview',
  'final_round',
  'offer',
  'rejected',
  'ghosted',
] as const

export const PIPELINE_LABELS: Record<string, string> = {
  saved: 'Saved',
  applied: 'Applied',
  phone_screen: 'Phone Screen',
  interview: 'Interview',
  final_round: 'Final Round',
  offer: 'Offer',
  rejected: 'Rejected',
  ghosted: 'Ghosted',
}

export const EXPERIENCE_LEVELS = ['entry', 'mid', 'senior', 'exec'] as const
export const REMOTE_TYPES = ['remote', 'hybrid', 'onsite'] as const
export const POSTED_WITHIN_OPTIONS = [
  { label: 'Today', value: 1 },
  { label: '3 days', value: 3 },
  { label: '7 days', value: 7 },
  { label: '14 days', value: 14 },
  { label: '30 days', value: 30 },
]
