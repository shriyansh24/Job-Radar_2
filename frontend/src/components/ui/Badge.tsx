import { cn } from '../../lib/utils';

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
  children: React.ReactNode;
  className?: string;
}

export default function Badge({ variant = 'default', size = 'sm', children, className }: BadgeProps) {
  const variants = {
    default: 'bg-bg-tertiary text-text-secondary border-border',
    success: 'bg-accent-success/15 text-accent-success border-accent-success/30',
    warning: 'bg-accent-warning/15 text-accent-warning border-accent-warning/30',
    danger: 'bg-accent-danger/15 text-accent-danger border-accent-danger/30',
    info: 'bg-accent-primary/15 text-accent-primary border-accent-primary/30',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full border',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
}
