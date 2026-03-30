import { useState } from "react";
import { X } from "@phosphor-icons/react";
import Input from "../ui/Input";
import { cn } from "../../lib/utils";
import { CHIP } from "./autoApplyUtils";

export function KeywordInput({
  label,
  keywords,
  onChange,
  placeholder,
}: {
  label: string;
  keywords: string[];
  onChange: (keywords: string[]) => void;
  placeholder: string;
}) {
  const [inputValue, setInputValue] = useState("");

  function addKeyword() {
    const trimmed = inputValue.trim();
    if (!trimmed || keywords.includes(trimmed)) {
      return;
    }

    onChange([...keywords, trimmed]);
    setInputValue("");
  }

  function removeKeyword(keyword: string) {
    onChange(keywords.filter((value) => value !== keyword));
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-text-secondary">{label}</label>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          placeholder={placeholder}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addKeyword();
            }
          }}
        />
        <button
          type="button"
          onClick={addKeyword}
          disabled={!inputValue.trim()}
          className="hard-press border-2 border-border bg-card px-4 py-2.5 text-[10px] font-bold uppercase tracking-[0.18em] text-text-secondary hover:text-text-primary disabled:opacity-50"
        >
          Add
        </button>
      </div>
      {keywords.length ? (
        <div className="flex flex-wrap gap-2">
          {keywords.map((keyword) => (
            <span key={keyword} className={cn(CHIP, "bg-background text-text-primary")}>
              {keyword}
              <button
                type="button"
                onClick={() => removeKeyword(keyword)}
                className="inline-flex size-4 items-center justify-center border-l-2 border-[var(--color-text-primary)] pl-1 text-text-muted transition-colors hover:text-accent-danger"
              >
                <X size={10} weight="bold" />
              </button>
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
