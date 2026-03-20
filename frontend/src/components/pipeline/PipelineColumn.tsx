import Badge from '../ui/Badge';
import { SkeletonCard } from '../ui/Skeleton';
import { cn } from '../../lib/utils';
import type { Application } from '../../api/pipeline';
import ApplicationCard from './ApplicationCard';

interface PipelineColumnProps {
  label: string;
  color: string;
  apps: Application[];
  loading: boolean;
  onTransition: (appId: string, newStatus: string) => void;
  onViewHistory: (app: Application) => void;
}

export default function PipelineColumn({
  label,
  color,
  apps,
  loading,
  onTransition,
  onViewHistory,
}: PipelineColumnProps) {
  return (
    <div
      className={cn(
        "w-[320px] flex flex-col bg-bg-secondary/60 supports-[backdrop-filter]:bg-bg-secondary/45 backdrop-blur rounded-[var(--radius-xl)] border border-border",
        "shadow-[var(--shadow-sm)]"
      )}
    >
      <div className={cn("border-t-2 rounded-t-[var(--radius-xl)]", color)} />
      <div className="flex items-center justify-between px-5 py-4 shrink-0">
        <div className="min-w-0">
          <div className="text-xs font-medium text-text-muted tracking-tight">
            Stage
          </div>
          <span className="text-sm font-semibold text-text-primary truncate">
            {label}
          </span>
        </div>
        <Badge size="sm">
          <span className="font-mono">{apps.length}</span>
        </Badge>
      </div>
      <div className="flex-1 overflow-auto px-3 pb-3">
        {loading ? (
          Array.from({ length: 2 }).map((_, i) => <SkeletonCard key={i} />)
        ) : apps.length === 0 ? (
          <p className="text-xs text-text-muted text-center py-4">No applications</p>
        ) : (
          apps.map((app) => (
            <ApplicationCard
              key={app.id}
              app={app}
              onTransition={(newStatus) => onTransition(app.id, newStatus)}
              onViewHistory={() => onViewHistory(app)}
            />
          ))
        )}
      </div>
    </div>
  );
}
