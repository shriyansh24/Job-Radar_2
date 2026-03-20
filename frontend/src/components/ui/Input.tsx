import { forwardRef } from "react";
import { cn } from "../../lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
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
            className={cn(
              "w-full bg-bg-secondary border border-border rounded-[var(--radius-md)] px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none transition-[border-color,box-shadow,background-color] duration-[var(--transition-fast)] focus:border-border-focus focus:ring-2 focus:ring-border-focus/25",
              icon && "pl-10",
              error &&
                "border-accent-danger focus:border-accent-danger focus:ring-accent-danger/20",
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
