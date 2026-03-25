import { cn } from '../../lib/utils';
import Button from './Button';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export default function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "border-2 border-border bg-card px-6 py-10 text-center shadow-[var(--shadow-sm)]",
        className
      )}
    >
      {icon && (
        <div className="mb-4 inline-flex size-14 items-center justify-center border-2 border-border bg-[var(--color-bg-tertiary)] text-text-muted shadow-[var(--shadow-xs)]">
          {icon}
        </div>
      )}
      <h3 className="text-xl font-black uppercase tracking-[-0.05em] text-text-primary">{title}</h3>
      {description && (
        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-text-muted">{description}</p>
      )}
      {action && (
        <Button variant="primary" onClick={action.onClick} className="mt-6">
          {action.label}
        </Button>
      )}
    </div>
  );
}
