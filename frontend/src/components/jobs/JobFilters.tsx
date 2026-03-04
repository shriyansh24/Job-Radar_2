import { useState } from 'react'
import { Search, Filter, ChevronDown, Save, X } from 'lucide-react'
import { useJobStore } from '../../store/useJobStore'
import { createSavedSearch } from '../../api/client'
import { EXPERIENCE_LEVELS, REMOTE_TYPES, POSTED_WITHIN_OPTIONS, SOURCE_COLORS } from '../../lib/constants'
import { cn } from '../../lib/utils'
import toast from 'react-hot-toast'

const SOURCES = ['serpapi', 'greenhouse', 'lever', 'ashby', 'jobspy', 'theirstack']

export default function JobFilters() {
  const { filters, setFilters, resetFilters, isFilterPanelOpen, isResumeActive } = useJobStore()
  const [searchInput, setSearchInput] = useState(filters.q || '')
  const [saveSearchName, setSaveSearchName] = useState('')
  const [showSaveDialog, setShowSaveDialog] = useState(false)

  const handleSearch = () => setFilters({ q: searchInput || undefined })

  const toggleSource = (source: string) => {
    const current = filters.source?.split(',').filter(Boolean) || []
    const next = current.includes(source)
      ? current.filter((s) => s !== source)
      : [...current, source]
    setFilters({ source: next.length ? next.join(',') : undefined })
  }

  const toggleLevel = (level: string) => {
    const current = filters.experience_level?.split(',').filter(Boolean) || []
    const next = current.includes(level)
      ? current.filter((l) => l !== level)
      : [...current, level]
    setFilters({ experience_level: next.length ? next.join(',') : undefined })
  }

  const toggleRemote = (type: string) => {
    const current = filters.remote_type?.split(',').filter(Boolean) || []
    const next = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type]
    setFilters({ remote_type: next.length ? next.join(',') : undefined })
  }

  const handleSaveSearch = async () => {
    if (!saveSearchName.trim()) return
    try {
      await createSavedSearch({
        name: saveSearchName,
        query_params: filters,
      })
      toast.success('Search saved')
      setShowSaveDialog(false)
      setSaveSearchName('')
    } catch {
      toast.error('Failed to save search')
    }
  }

  if (!isFilterPanelOpen) return null

  return (
    <div className="w-[280px] flex-shrink-0 bg-surface border-r border-border p-4 space-y-5 overflow-y-auto">
      {/* Search */}
      <div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input
            type="text"
            placeholder="Search jobs..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full bg-elevated border border-border rounded-lg pl-9 pr-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent"
          />
        </div>
      </div>

      {/* Source checkboxes */}
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">Source</h3>
        <div className="space-y-1">
          {SOURCES.map((source) => {
            const active = filters.source?.includes(source) ?? false
            return (
              <button
                key={source}
                onClick={() => toggleSource(source)}
                className={cn(
                  'w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors',
                  active ? 'bg-elevated text-text-primary' : 'text-text-secondary hover:bg-elevated/50'
                )}
              >
                <span
                  className={cn(
                    'w-3 h-3 rounded border flex items-center justify-center',
                    active ? 'bg-accent border-accent' : 'border-border'
                  )}
                >
                  {active && <span className="text-white text-[8px]">&#10003;</span>}
                </span>
                <span className="capitalize">{source}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Experience Level */}
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">Experience</h3>
        <div className="flex flex-wrap gap-1">
          {EXPERIENCE_LEVELS.map((level) => {
            const active = filters.experience_level?.includes(level) ?? false
            return (
              <button
                key={level}
                onClick={() => toggleLevel(level)}
                className={cn(
                  'px-2.5 py-1 rounded-full text-xs border transition-colors capitalize',
                  active
                    ? 'bg-accent/10 text-accent border-accent/30'
                    : 'border-border text-text-secondary hover:border-text-secondary'
                )}
              >
                {level}
              </button>
            )
          })}
        </div>
      </div>

      {/* Remote Type */}
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">Remote</h3>
        <div className="flex flex-wrap gap-1">
          {REMOTE_TYPES.map((type) => {
            const active = filters.remote_type?.includes(type) ?? false
            return (
              <button
                key={type}
                onClick={() => toggleRemote(type)}
                className={cn(
                  'px-2.5 py-1 rounded-full text-xs border transition-colors capitalize',
                  active
                    ? 'bg-accent/10 text-accent border-accent/30'
                    : 'border-border text-text-secondary hover:border-text-secondary'
                )}
              >
                {type}
              </button>
            )
          })}
        </div>
      </div>

      {/* Posted Within */}
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">Posted Within</h3>
        <div className="flex flex-wrap gap-1">
          {POSTED_WITHIN_OPTIONS.map((opt) => {
            const active = filters.posted_within_days === opt.value
            return (
              <button
                key={opt.value}
                onClick={() =>
                  setFilters({ posted_within_days: active ? undefined : opt.value })
                }
                className={cn(
                  'px-2.5 py-1 rounded-full text-xs border transition-colors',
                  active
                    ? 'bg-accent/10 text-accent border-accent/30'
                    : 'border-border text-text-secondary hover:border-text-secondary'
                )}
              >
                {opt.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Match score slider */}
      {isResumeActive && (
        <div>
          <h3 className="text-xs font-semibold text-text-secondary uppercase mb-2">
            Min Match Score: {filters.min_match_score ?? 0}%
          </h3>
          <input
            type="range"
            min={0}
            max={100}
            value={filters.min_match_score ?? 0}
            onChange={(e) => setFilters({ min_match_score: Number(e.target.value) || undefined })}
            className="w-full accent-accent"
          />
        </div>
      )}

      {/* Actions */}
      <div className="space-y-2 pt-2 border-t border-border">
        {showSaveDialog ? (
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Search name..."
              value={saveSearchName}
              onChange={(e) => setSaveSearchName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveSearch()}
              className="w-full bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSaveSearch}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-accent text-white rounded-lg text-xs"
              >
                <Save size={12} /> Save
              </button>
              <button
                onClick={() => setShowSaveDialog(false)}
                className="px-3 py-1.5 border border-border rounded-lg text-xs text-text-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => setShowSaveDialog(true)}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 border border-border rounded-lg text-xs text-text-secondary hover:text-text-primary"
            >
              <Save size={12} /> Save Search
            </button>
            <button
              onClick={resetFilters}
              className="px-3 py-1.5 border border-border rounded-lg text-xs text-text-secondary hover:text-text-primary"
            >
              Reset
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
