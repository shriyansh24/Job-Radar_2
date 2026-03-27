import { Plus, X } from "@phosphor-icons/react";
import { useState } from "react";
import { Button } from "../ui/Button";
import Input from "../ui/Input";
import { cn } from "../../lib/utils";

const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";

export function TagRow({
  label,
  placeholder,
  items,
  onAdd,
  onRemove,
}: {
  label: string;
  placeholder: string;
  items: string[];
  onAdd: (value: string) => void;
  onRemove: (index: number) => void;
}) {
  const [value, setValue] = useState("");

  function commitValue() {
    const trimmed = value.trim();
    if (!trimmed) {
      return;
    }

    onAdd(trimmed);
    setValue("");
  }

  return (
    <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] p-4 shadow-[4px_4px_0px_0px_var(--color-text-primary)] sm:p-5">
      <div className="flex flex-col gap-4">
        <div className="space-y-1">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">{label}</div>
          <p className="text-sm leading-6 text-text-secondary">
            Add concise handles. One strong seed is better than a paragraph.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder={placeholder}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                commitValue();
              }
            }}
          />
          <Button type="button" variant="secondary" icon={<Plus size={14} weight="bold" />} onClick={commitValue}>
            Add
          </Button>
        </div>

        {items.length ? (
          <div className="flex flex-wrap gap-2">
            {items.map((item, index) => (
              <span key={`${item}-${index}`} className={cn(CHIP, "bg-bg-secondary text-text-primary")}>
                {item}
                <button
                  type="button"
                  onClick={() => onRemove(index)}
                  className="inline-flex size-4 items-center justify-center border-l-2 border-[var(--color-text-primary)] pl-1 text-text-muted transition-colors hover:text-accent-danger"
                  aria-label={`Remove ${item}`}
                >
                  <X size={10} weight="bold" />
                </button>
              </span>
            ))}
          </div>
        ) : (
          <div className="border-2 border-dashed border-[var(--color-text-primary)] bg-background px-4 py-5 text-sm text-text-muted">
            No entries yet.
          </div>
        )}
      </div>
    </div>
  );
}
