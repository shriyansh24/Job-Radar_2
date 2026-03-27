import { Plus, X } from "@phosphor-icons/react";
import { useState } from "react";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Input from "../ui/Input";
import type React from "react";
import { BRUTAL_BUTTON, BRUTAL_FIELD, BRUTAL_PANEL_ALT } from "./constants";

function ToggleGroup({
  label,
  options,
  selected,
  onChange,
}: {
  label: string;
  options: { value: string; label: string }[];
  selected: string[];
  onChange: (values: string[]) => void;
}) {
  function toggle(value: string) {
    onChange(selected.includes(value) ? selected.filter((item) => item !== value) : [...selected, value]);
  }

  return (
    <div>
      <label className="mb-2 block text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => toggle(option.value)}
            className={
              selected.includes(option.value)
                ? "border-2 border-[var(--color-text-primary)] bg-[var(--color-accent-primary-subtle)] px-3 py-2 text-sm font-bold uppercase tracking-[0.08em] text-[var(--color-accent-primary)]"
                : "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm font-bold uppercase tracking-[0.08em] text-[var(--color-text-muted)] transition-transform hover:-translate-x-[1px] hover:-translate-y-[1px] hover:text-[var(--color-text-primary)]"
            }
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function TagEditor({
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

  function addItem() {
    const trimmed = value.trim();
    if (!trimmed || items.includes(trimmed)) return;
    onAdd(trimmed);
    setValue("");
  }

  return (
    <div className="space-y-2">
      <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">{label}</label>
      <div className="flex gap-2">
        <Input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addItem();
            }
          }}
          placeholder={placeholder}
          className={BRUTAL_FIELD}
        />
        <Button type="button" variant="secondary" className={BRUTAL_BUTTON} icon={<Plus size={14} weight="bold" />} onClick={addItem}>
          Add
        </Button>
      </div>
      {items.length ? (
        <div className="flex flex-wrap gap-2">
          {items.map((item, index) => (
            <Badge key={`${item}-${index}`} variant="info" size="md" className="rounded-none">
              <span className="flex items-center gap-1.5">
                {item}
                <button type="button" onClick={() => onRemove(index)} className="hover:text-[var(--color-accent-danger)]">
                  <X size={12} weight="bold" />
                </button>
              </span>
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function EntryCard({
  title,
  children,
  onRemove,
}: {
  title: string;
  children: React.ReactNode;
  onRemove: () => void;
}) {
  return (
    <div className={BRUTAL_PANEL_ALT}>
      <div className="flex items-start justify-between gap-3 p-4">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-bold uppercase tracking-[0.08em] text-foreground">{title}</div>
          <div className="mt-3">{children}</div>
        </div>
        <button type="button" onClick={onRemove} className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-2 py-1 text-[var(--color-text-muted)] hover:text-[var(--color-accent-danger)]">
          <X size={16} weight="bold" />
        </button>
      </div>
    </div>
  );
}

export { ToggleGroup, TagEditor, EntryCard };
