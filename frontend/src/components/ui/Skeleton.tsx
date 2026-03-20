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
        'animate-pulse bg-bg-tertiary',
        variant === 'text' && 'h-4 rounded-[var(--radius-sm)]',
        variant === 'rect' && 'rounded-[var(--radius-md)]',
        variant === 'circle' && 'rounded-full',
        className
      )}
      style={{ width, height }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-bg-secondary border border-border rounded-[var(--radius-lg)] p-4 space-y-3">
      <Skeleton variant="text" className="w-3/4" />
      <Skeleton variant="text" className="w-1/2" />
      <Skeleton variant="rect" className="w-full h-20" />
    </div>
  );
}
