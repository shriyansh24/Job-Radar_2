import { clsx } from 'clsx';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  className?: string;
}

export default function Toggle({ checked, onChange, label, disabled, className }: ToggleProps) {
  return (
    <label className={clsx('inline-flex items-center gap-3 cursor-pointer', disabled && 'opacity-50 cursor-not-allowed', className)}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={clsx(
          'hard-press relative inline-flex h-7 w-14 shrink-0 border-2 border-border shadow-none transition-colors duration-200 focus:outline-none',
          checked ? 'bg-accent-primary text-primary-foreground' : 'bg-card'
        )}
      >
        <span
          className={clsx(
            'pointer-events-none absolute left-1 top-1 inline-block h-4 w-4 transform border-2 border-border bg-background transition-transform duration-200',
            checked ? 'translate-x-7' : 'translate-x-0'
          )}
        />
      </button>
      {label && <span className="text-sm font-medium text-text-primary">{label}</span>}
    </label>
  );
}
