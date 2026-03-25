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
            className="mb-2 block font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted"
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
              "w-full border-2 border-border bg-[var(--color-bg-secondary)] px-3 py-3 text-sm text-text-primary placeholder:text-text-muted outline-none transition-[border-color,box-shadow,background-color] duration-[var(--transition-fast)] focus:border-border-focus focus:bg-[var(--color-bg-tertiary)] focus:shadow-[var(--shadow-blue)]",
              icon && "pl-10",
              error &&
                "border-accent-danger focus:border-accent-danger focus:shadow-none",
              className
            )}
            {...props}
          />
        </div>
        {error && <p className="mt-1 text-xs text-accent-danger">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
