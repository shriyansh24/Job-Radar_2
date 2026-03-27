import { cn } from '../../lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rect' | 'circle';
  width?: string;
  height?: string;
}

export default function Skeleton({ className, variant = 'rect', width, height }: SkeletonProps) {
  return (
    <div
      className={cn(
        'skeleton border border-border/40',
        variant === 'text' && 'h-4 rounded-none',
        variant === 'rect' && 'rounded-none',
        variant === 'circle' && 'rounded-full',
        className
      )}
      style={{ width, height }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="space-y-3 border-2 border-border bg-card p-4 shadow-[var(--shadow-sm)]">
      <Skeleton variant="text" className="w-3/4" />
      <Skeleton variant="text" className="w-1/2" />
      <Skeleton variant="rect" className="w-full h-20" />
    </div>
  );
}
