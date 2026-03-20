import { Funnel, MagnifyingGlass } from "@phosphor-icons/react";
import type { JobListParams } from "../../api/jobs";
import { useJobStore } from "../../store/useJobStore";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Select from "../ui/Select";

const sourceOptions = [
  { value: '', label: 'All Sources' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'indeed', label: 'Indeed' },
  { value: 'glassdoor', label: 'Glassdoor' },
  { value: 'theirstack', label: 'TheirStack' },
  { value: 'career_page', label: 'Career Page' },
];

const remoteOptions = [
  { value: '', label: 'All Remote Types' },
  { value: 'remote', label: 'Remote' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'onsite', label: 'On-site' },
];

const experienceOptions = [
  { value: '', label: 'All Levels' },
  { value: 'entry', label: 'Entry' },
  { value: 'mid', label: 'Mid' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
  { value: 'executive', label: 'Executive' },
];

const sortOptions = [
  { value: 'scraped_at', label: 'Date' },
  { value: 'match_score', label: 'Match Score' },
  { value: 'tfidf_score', label: 'TF-IDF Score' },
  { value: 'company_name', label: 'Company' },
];

interface JobFiltersProps {
  searchInput: string;
  onSearchChange: (value: string) => void;
  showFilters: boolean;
  onToggleFilters: () => void;
  filters: JobListParams;
  onFiltersChange: (filters: Partial<JobListParams>) => void;
}

export default function JobFilters({
  searchInput,
  onSearchChange,
  showFilters,
  onToggleFilters,
  filters,
  onFiltersChange,
}: JobFiltersProps) {
  return (
    <div className="shrink-0 space-y-3 mb-4">
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search jobs..."
            icon={<MagnifyingGlass size={16} weight="bold" />}
            value={searchInput}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>
        <Button
          variant="secondary"
          onClick={onToggleFilters}
          icon={<Funnel size={16} weight="bold" />}
        >
          Filters
        </Button>
      </div>

      {showFilters && (
        <div className="flex flex-wrap gap-3 p-4 bg-bg-secondary border border-border rounded-[var(--radius-xl)] shadow-[var(--shadow-sm)]">
          <div className="w-40">
            <Select
              options={sourceOptions}
              value={filters.source || ''}
              onChange={(e) => onFiltersChange({ source: e.target.value || undefined })}
            />
          </div>
          <div className="w-40">
            <Select
              options={remoteOptions}
              value={filters.remote_type || ''}
              onChange={(e) => onFiltersChange({ remote_type: e.target.value || undefined })}
            />
          </div>
          <div className="w-40">
            <Select
              options={experienceOptions}
              value={filters.experience_level || ''}
              onChange={(e) => onFiltersChange({ experience_level: e.target.value || undefined })}
            />
          </div>
          <div className="w-40">
            <Select
              options={sortOptions}
              value={filters.sort_by || 'scraped_at'}
              onChange={(e) => onFiltersChange({ sort_by: e.target.value })}
            />
          </div>
          <Button variant="ghost" size="sm" onClick={() => useJobStore.getState().resetFilters()}>
            Clear
          </Button>
        </div>
      )}
    </div>
  );
}
