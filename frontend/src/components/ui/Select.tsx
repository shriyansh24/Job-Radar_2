import { CaretDown } from "@phosphor-icons/react";
import { forwardRef } from "react";
import { cn } from "../../lib/utils";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            className={cn(
              "w-full appearance-none bg-bg-secondary border border-border rounded-[var(--radius-md)] px-3 py-2 pr-9 text-sm text-text-primary outline-none transition-[border-color,box-shadow,background-color] duration-[var(--transition-fast)] focus:border-border-focus focus:ring-2 focus:ring-border-focus/25",
              error && "border-accent-danger focus:border-accent-danger focus:ring-accent-danger/20",
              className
            )}
            {...props}
          >
            {placeholder && (
              <option value="" className="text-text-muted">
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <CaretDown
            size={16}
            weight="bold"
            className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none"
          />
        </div>
        {error && <p className="mt-1 text-xs text-accent-danger">{error}</p>}
      </div>
    );
  }
);

Select.displayName = "Select";
export default Select;
