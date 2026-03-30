import { forwardRef, useId } from 'react';
import { cn } from '../../lib/utils';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className, ...props }, ref) => {
    const generatedId = useId();
    const textareaId = props.id ?? generatedId;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="mb-2 block font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={cn(
            'min-h-[96px] w-full resize-y border-2 border-border bg-[var(--color-bg-secondary)] px-3 py-3 text-sm text-text-primary placeholder:text-text-muted outline-none transition-[border-color,box-shadow,background-color,color] duration-[var(--transition-fast)] focus:border-border-focus focus:bg-[var(--color-bg-elevated)] focus:shadow-[var(--shadow-blue)] aria-invalid:border-[var(--color-accent-danger)] aria-invalid:shadow-none',
            error && 'border-accent-danger focus:border-accent-danger focus:shadow-none',
            className
          )}
          aria-invalid={error ? true : props["aria-invalid"]}
          {...props}
        />
        {error && <p className="mt-1 text-[11px] font-medium text-accent-danger">{error}</p>}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
export default Textarea;
