import { useRef, useEffect, useState } from 'react'
import { TerminalSquare, ChevronDown, Pause, Play, X } from 'lucide-react'
import { useJobStore } from '../../store/useJobStore'
import { cn } from '../../lib/utils'

export default function ScraperLog() {
  const { scraperLogs, isLogDrawerOpen, setIsLogDrawerOpen } = useJobStore()
  const scrollRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [scraperLogs, autoScroll])

  const handleScroll = () => {
    if (!scrollRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 50)
  }

  if (scraperLogs.length === 0 && !isLogDrawerOpen) return null

  return (
    <div
      className={cn(
        'fixed bottom-4 right-4 z-50 rounded-xl border border-border bg-surface shadow-2xl transition-all duration-300',
        isLogDrawerOpen ? 'w-[600px] h-[200px]' : 'w-[600px] h-[40px]'
      )}
    >
      {/* Header bar */}
      <div
        className="flex items-center justify-between px-3 h-[40px] cursor-pointer border-b border-border"
        onClick={() => setIsLogDrawerOpen(!isLogDrawerOpen)}
      >
        <div className="flex items-center gap-2">
          <TerminalSquare size={14} className="text-text-secondary" />
          <span className="text-xs font-medium text-text-secondary">Scraper Log</span>
          <span className="text-xs font-mono text-text-secondary">
            ({scraperLogs.length})
          </span>
        </div>
        <div className="flex items-center gap-1">
          {isLogDrawerOpen && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setAutoScroll(!autoScroll)
              }}
              className="p-1 rounded hover:bg-elevated text-text-secondary"
            >
              {autoScroll ? <Pause size={12} /> : <Play size={12} />}
            </button>
          )}
          <ChevronDown
            size={14}
            className={cn(
              'text-text-secondary transition-transform',
              !isLogDrawerOpen && 'rotate-180'
            )}
          />
        </div>
      </div>

      {/* Log content */}
      {isLogDrawerOpen && (
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="h-[158px] overflow-auto px-3 py-2 font-mono text-xs"
        >
          {scraperLogs.map((log, i) => (
            <div key={i} className="flex gap-2 py-0.5">
              <span className="text-text-secondary flex-shrink-0">[{log.timestamp}]</span>
              <span className="text-accent-cyan flex-shrink-0 w-24 text-right">
                {log.source}
              </span>
              <span className="text-text-secondary flex-shrink-0">&rarr;</span>
              <span
                className={cn(
                  log.type === 'success' && 'text-accent-green',
                  log.type === 'error' && 'text-accent-red',
                  log.type === 'info' && 'text-text-secondary'
                )}
              >
                {log.message}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
