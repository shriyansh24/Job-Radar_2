import { MagnifyingGlass } from "@phosphor-icons/react";
import type { JobListParams } from "../../api/jobs";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Select from "../ui/Select";
import { SOURCE_OPTIONS, REMOTE_OPTIONS, EXPERIENCE_OPTIONS, SORT_OPTIONS, type SearchMode } from "./jobBoardUtils";

interface JobBoardFiltersProps {
  searchMode: SearchMode;
  searchInput: string;
  onSearchChange: (value: string) => void;
  showFilters: boolean;
  filters: JobListParams;
  onFiltersChange: (filters: Partial<JobListParams>) => void;
  onClearFilters: () => void;
}

export function JobBoardFilters({
  searchMode,
  searchInput,
  onSearchChange,
  showFilters,
  filters,
  onFiltersChange,
  onClearFilters,
}: JobBoardFiltersProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.35fr)_repeat(3,minmax(160px,1fr))]">
        <Input
          placeholder={searchMode === "semantic" ? "Describe a role, company, or stack" : "Search jobs"}
          icon={<MagnifyingGlass size={16} weight="bold" />}
          value={searchInput}
          onChange={(event) => onSearchChange(event.target.value)}
        />
        <Select
          options={SOURCE_OPTIONS}
          value={filters.source || ""}
          onChange={(event) => onFiltersChange({ source: event.target.value || undefined })}
        />
        <Select
          options={REMOTE_OPTIONS}
          value={filters.remote_type || ""}
          onChange={(event) => onFiltersChange({ remote_type: event.target.value || undefined })}
        />
        <Select
          options={EXPERIENCE_OPTIONS}
          value={filters.experience_level || ""}
          onChange={(event) => onFiltersChange({ experience_level: event.target.value || undefined })}
        />
      </div>

      {showFilters ? (
        <div className="mt-4 flex flex-wrap items-center gap-3 border-t-2 border-border pt-4">
          <div className="min-w-[180px]">
            <Select
              options={SORT_OPTIONS}
              value={filters.sort_by || "scraped_at"}
              onChange={(event) => onFiltersChange({ sort_by: event.target.value })}
            />
          </div>
          <Button variant="secondary" size="sm" onClick={onClearFilters}>
            Clear filters
          </Button>
          {searchMode === "semantic" ? (
            <span className="inline-flex items-center border-2 border-border bg-bg-secondary px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]">
              Semantic search uses one list
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
