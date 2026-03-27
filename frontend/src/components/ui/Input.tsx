import { forwardRef, useId } from "react";
import { cn } from "../../lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className, ...props }, ref) => {
    const generatedId = useId();
    const inputId = props.id ?? generatedId;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="mb-2 block font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              "min-h-11 w-full border-2 border-border bg-[var(--color-bg-secondary)] px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted outline-none transition-[border-color,box-shadow,background-color,color] duration-[var(--transition-fast)] focus:border-border-focus focus:bg-[var(--color-bg-elevated)] focus:shadow-[var(--shadow-blue)] aria-invalid:border-[var(--color-accent-danger)] aria-invalid:shadow-none",
              icon && "pl-10",
              error &&
                "border-accent-danger focus:border-accent-danger focus:shadow-none",
              className
            )}
            aria-invalid={error ? true : props["aria-invalid"]}
            {...props}
          />
        </div>
        {error && <p className="mt-1 text-[11px] font-medium text-accent-danger">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
