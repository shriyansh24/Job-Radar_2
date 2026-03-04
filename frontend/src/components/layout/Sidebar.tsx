import { LayoutGrid, List, KanbanSquare, BarChart3, Settings } from 'lucide-react'
import { cn } from '../../lib/utils'

type Page = 'dashboard' | 'jobs' | 'pipeline' | 'analytics' | 'settings'

const NAV_ITEMS: { page: Page; label: string; icon: typeof LayoutGrid }[] = [
  { page: 'dashboard', label: 'Dashboard', icon: LayoutGrid },
  { page: 'jobs', label: 'Job Board', icon: List },
  { page: 'pipeline', label: 'Pipeline', icon: KanbanSquare },
  { page: 'analytics', label: 'Analytics', icon: BarChart3 },
  { page: 'settings', label: 'Settings', icon: Settings },
]

interface SidebarProps {
  currentPage: Page
  onNavigate: (page: Page) => void
}

export default function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  return (
    <aside className="w-60 h-screen bg-surface border-r border-border flex flex-col">
      {/* Logo area handled by TopBar */}
      <div className="h-14" />

      <nav className="flex-1 px-3 py-2 space-y-1">
        {NAV_ITEMS.map(({ page, label, icon: Icon }) => (
          <button
            key={page}
            onClick={() => onNavigate(page)}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
              currentPage === page
                ? 'bg-elevated text-text-primary'
                : 'text-text-secondary hover:text-text-primary hover:bg-elevated/50'
            )}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-border">
        <div className="text-xs text-text-secondary font-mono">v0.1.0</div>
        <div className="text-xs text-text-secondary mt-1 flex items-center gap-1">
          Local Only <span className="text-accent-green">&#x1f512;</span>
        </div>
      </div>
    </aside>
  )
}
