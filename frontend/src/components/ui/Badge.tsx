import { cn } from '../../lib/utils';

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
  children: React.ReactNode;
  className?: string;
}

export default function Badge({ variant = 'default', size = 'sm', children, className }: BadgeProps) {
  const variants = {
    default: 'bg-[var(--color-bg-tertiary)] text-foreground border-border',
    success: 'bg-[var(--color-accent-success-subtle)] text-[var(--color-accent-success)] border-border',
    warning: 'bg-[var(--color-accent-warning-subtle)] text-[var(--color-accent-warning)] border-border',
    danger: 'bg-[var(--color-accent-danger-subtle)] text-[var(--color-accent-danger)] border-border',
    info: 'bg-[var(--color-accent-primary-subtle)] text-[var(--color-accent-primary)] border-border',
  };

  const sizes = {
    sm: 'px-2 py-1 text-[10px]',
    md: 'px-3 py-1.5 text-[11px]',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center border-2 font-mono font-bold uppercase tracking-[0.16em] rounded-none',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
}
