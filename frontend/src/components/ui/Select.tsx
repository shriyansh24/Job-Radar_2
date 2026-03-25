import { CaretDown } from "@phosphor-icons/react";
import { forwardRef, useId } from "react";
import { cn } from "../../lib/utils";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className, ...props }, ref) => {
    const generatedId = useId();
    const selectId = props.id ?? generatedId;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={selectId}
            className="mb-2 block font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={cn(
              "w-full appearance-none border-2 border-border bg-[var(--color-bg-secondary)] px-3 py-3 pr-10 text-sm text-text-primary outline-none transition-[border-color,box-shadow,background-color] duration-[var(--transition-fast)] focus:border-border-focus focus:bg-[var(--color-bg-tertiary)] focus:shadow-[var(--shadow-blue)]",
              error && "border-accent-danger focus:border-accent-danger focus:shadow-none",
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
