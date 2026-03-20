import { cn } from '../../lib/utils';

interface ScoreGaugeProps {
  score: number;
  label: string;
  className?: string;
}

export default function ScoreGauge({ score, label, className }: ScoreGaugeProps) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? 'bg-accent-success' : pct >= 50 ? 'bg-accent-warning' : 'bg-accent-danger';
  const textColor = pct >= 80 ? 'text-accent-success' : pct >= 50 ? 'text-accent-warning' : 'text-accent-danger';

  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">{label}</span>
        <span className={cn('text-sm font-medium', textColor)}>{pct}%</span>
      </div>
      <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full transition-all', color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
