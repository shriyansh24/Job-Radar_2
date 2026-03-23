import {
  Briefcase,
  CaretLeft,
  CaretRight,
  Funnel,
  MagnifyingGlass,
  Sparkle,
  Star,
} from "@phosphor-icons/react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { jobsApi, type Job, type JobListParams } from "../api/jobs";
import JobDetail from "../components/jobs/JobDetail";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import { PageHeader, SplitWorkspace, StateBlock, Surface } from "../components/system";
import { useDebounce } from "../hooks/useDebounce";
import { cn } from "../lib/utils";
import { useJobStore } from "../store/useJobStore";

const sourceOptions = [
  { value: "", label: "All sources" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "indeed", label: "Indeed" },
  { value: "glassdoor", label: "Glassdoor" },
  { value: "theirstack", label: "TheirStack" },
  { value: "career_page", label: "Career page" },
];

const remoteOptions = [
  { value: "", label: "All remote types" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const experienceOptions = [
  { value: "", label: "All levels" },
  { value: "entry", label: "Entry" },
  { value: "mid", label: "Mid" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead" },
  { value: "executive", label: "Executive" },
];

const sortOptions = [
  { value: "scraped_at", label: "Date" },
  { value: "match_score", label: "Match score" },
  { value: "tfidf_score", label: "TF-IDF score" },
  { value: "company_name", label: "Company" },
];

type SearchMode = "exact" | "semantic";

function JobRow({
  job,
  selected,
  onClick,
}: {
  job: Job;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full flex-col gap-3 rounded-[var(--radius-lg)] border px-4 py-4 text-left transition-colors",
        selected
          ? "border-accent-primary/30 bg-accent-primary/8"
          : "border-transparent bg-bg-secondary hover:border-border hover:bg-bg-hover"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-text-primary">{job.title}</div>
          <div className="mt-1 truncate text-sm text-text-secondary">
            {job.company_name ?? "Unknown company"}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {job.match_score !== null ? (
            <Badge
              variant={
                job.match_score >= 0.8
                  ? "success"
                  : job.match_score >= 0.5
                    ? "warning"
                    : "danger"
              }
              size="sm"
            >
              {Math.round(job.match_score * 100)}%
            </Badge>
          ) : null}
          {job.is_starred ? (
            <Star size={14} weight="fill" className="text-accent-warning" />
          ) : null}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
        {job.location ? <span>{job.location}</span> : null}
        {job.remote_type ? <Badge size="sm">{job.remote_type}</Badge> : null}
        {job.job_type ? <Badge size="sm">{job.job_type}</Badge> : null}
        {job.source ? <Badge variant="info" size="sm">{job.source}</Badge> : null}
      </div>
    </button>
  );
}

export default function JobBoard() {
  const { selectedJobId, filters, setSelectedJob, setFilters } = useJobStore();
  const [searchInput, setSearchInput] = useState(filters.q || "");
  const [showFilters, setShowFilters] = useState(true);
  const [searchMode, setSearchMode] = useState<SearchMode>("exact");
  const debouncedSearch = useDebounce(searchInput, 250);

  const activeFilters: JobListParams = {
    ...filters,
    q: searchMode === "exact" ? debouncedSearch || undefined : undefined,
  };

  const exactQuery = useQuery({
    queryKey: ["jobs", activeFilters],
    queryFn: () => jobsApi.list(activeFilters).then((r) => r.data),
    placeholderData: keepPreviousData,
    enabled: searchMode === "exact",
  });

  const semanticQuery = useQuery({
    queryKey: ["jobs", "semantic", debouncedSearch],
    queryFn: () => jobsApi.semanticSearch(debouncedSearch, 20).then((r) => r.data),
    enabled: searchMode === "semantic" && debouncedSearch.trim().length > 1,
  });

  const jobs = searchMode === "semantic" ? semanticQuery.data ?? [] : exactQuery.data?.items ?? [];
  const total = searchMode === "semantic" ? semanticQuery.data?.length ?? 0 : exactQuery.data?.total ?? 0;
  const totalPages = searchMode === "semantic" ? 1 : exactQuery.data?.total_pages ?? 0;
  const currentPage = filters.page || 1;
  const isLoading = searchMode === "semantic" ? semanticQuery.isLoading : exactQuery.isLoading;
  const isError = searchMode === "semantic" ? semanticQuery.isError : exactQuery.isError;

  const { data: selectedJob, isLoading: isLoadingDetail } = useQuery({
    queryKey: ["job", selectedJobId],
    queryFn: () => jobsApi.get(selectedJobId!).then((r) => r.data),
    enabled: !!selectedJobId,
  });

  const firstJobId = jobs[0]?.id ?? null;
  const selectedJobVisible = selectedJobId ? jobs.some((job) => job.id === selectedJobId) : false;

  useEffect(() => {
    if (firstJobId && (!selectedJobId || !selectedJobVisible)) {
      setSelectedJob(firstJobId);
    }
  }, [firstJobId, selectedJobId, selectedJobVisible, setSelectedJob]);

  const activeFilterCount = [
    activeFilters.source,
    activeFilters.remote_type,
    activeFilters.experience_level,
    activeFilters.sort_by && activeFilters.sort_by !== "scraped_at" ? activeFilters.sort_by : null,
  ].filter(Boolean).length;

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <PageHeader
        eyebrow="Discover"
        title="Jobs"
        description="Search the feed with exact filters or semantic matching, then inspect the selected role in a live detail pane."
        actions={
          <>
            <Button
              variant={searchMode === "exact" ? "secondary" : "ghost"}
              onClick={() => setSearchMode("exact")}
              icon={<MagnifyingGlass size={16} weight="bold" />}
            >
              Exact
            </Button>
            <Button
              variant={searchMode === "semantic" ? "secondary" : "ghost"}
              onClick={() => setSearchMode("semantic")}
              icon={<Sparkle size={16} weight="bold" />}
            >
              Semantic
            </Button>
            <Button
              variant="secondary"
              onClick={() => setShowFilters((current) => !current)}
              icon={<Funnel size={16} weight="bold" />}
            >
              Filters
            </Button>
          </>
        }
        meta={
          <>
            <span>{total.toLocaleString()} results</span>
            <span>{activeFilterCount} active filters</span>
            <span>{searchMode === "semantic" ? "Semantic ranking" : `Page ${currentPage}`}</span>
          </>
        }
      />

      <Surface tone="default" radius="xl" padding="md">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_repeat(3,minmax(160px,1fr))]">
          <Input
            placeholder={searchMode === "semantic" ? "Describe the role you want..." : "Search jobs..."}
            icon={<MagnifyingGlass size={16} weight="bold" />}
            value={searchInput}
            onChange={(event) => {
              setSearchInput(event.target.value);
              setFilters({ q: event.target.value, page: 1 });
            }}
          />
          <Select
            options={sourceOptions}
            value={filters.source || ""}
            onChange={(event) => setFilters({ source: event.target.value || undefined, page: 1 })}
          />
          <Select
            options={remoteOptions}
            value={filters.remote_type || ""}
            onChange={(event) => setFilters({ remote_type: event.target.value || undefined, page: 1 })}
          />
          <Select
            options={experienceOptions}
            value={filters.experience_level || ""}
            onChange={(event) => setFilters({ experience_level: event.target.value || undefined, page: 1 })}
          />
        </div>

        {showFilters ? (
          <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-border pt-3">
            <div className="min-w-[180px]">
              <Select
                options={sortOptions}
                value={filters.sort_by || "scraped_at"}
                onChange={(event) => setFilters({ sort_by: event.target.value, page: 1 })}
              />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setFilters({
                  source: undefined,
                  remote_type: undefined,
                  experience_level: undefined,
                  sort_by: "scraped_at",
                  sort_order: "desc",
                  page: 1,
                });
                setSearchInput("");
                setSearchMode("exact");
              }}
            >
              Clear filters
            </Button>
            {searchMode === "semantic" ? (
              <span className="text-xs text-text-muted">
                Semantic search ranks the best matches and ignores pagination.
              </span>
            ) : null}
          </div>
        ) : null}
      </Surface>

      <SplitWorkspace
        primary={
          <Surface tone="default" radius="xl" padding="none" className="overflow-hidden">
            <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
              <div>
                <div className="text-xs font-medium uppercase tracking-[0.18em] text-text-muted">Results</div>
                <div className="mt-1 text-sm font-semibold text-text-primary">
                  {searchMode === "semantic" ? "Semantic matches" : "Job list"}
                </div>
              </div>
              <div className="text-xs text-text-muted">
                <span className="font-mono text-text-primary">{total}</span> total
              </div>
            </div>

            <div className="max-h-[72vh] overflow-auto p-3">
              {isError ? (
                <StateBlock
                  tone="danger"
                  title="Failed to load jobs"
                  description="Try again in a moment."
                />
              ) : isLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 8 }).map((_, index) => (
                    <div key={index} className="h-20 animate-pulse rounded-[var(--radius-lg)] bg-bg-hover/60" />
                  ))}
                </div>
              ) : jobs.length === 0 ? (
                <StateBlock
                  tone="muted"
                  icon={<Briefcase size={18} weight="bold" />}
                  title={searchMode === "semantic" ? "No semantic matches yet" : "No jobs found"}
                  description={
                    searchMode === "semantic"
                      ? "Try a broader description of the role, company, or stack."
                      : "Adjust the filters or search query to widen the feed."
                  }
                />
              ) : (
                <div className="space-y-2">
                  {jobs.map((job) => (
                    <JobRow
                      key={job.id}
                      job={job}
                      selected={job.id === selectedJobId}
                      onClick={() => setSelectedJob(job.id)}
                    />
                  ))}
                </div>
              )}
            </div>

            {!searchMode || searchMode === "exact" ? (
              totalPages > 1 ? (
                <div className="flex items-center justify-between border-t border-border px-5 py-3">
                  <span className="text-xs text-text-muted">
                    Page <span className="font-mono text-text-primary">{currentPage}</span> /{" "}
                    <span className="font-mono text-text-primary">{totalPages}</span>
                  </span>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={currentPage <= 1}
                      onClick={() => setFilters({ page: currentPage - 1 })}
                      icon={<CaretLeft size={14} weight="bold" />}
                    >
                      Prev
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={currentPage >= totalPages}
                      onClick={() => setFilters({ page: currentPage + 1 })}
                      icon={<CaretRight size={14} weight="bold" />}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              ) : null
            ) : null}
          </Surface>
        }
        secondary={
          <Surface tone="default" radius="xl" padding="none" className="overflow-hidden">
            {selectedJobId ? (
              isLoadingDetail ? (
                <div className="space-y-4 p-6">
                  <div className="h-8 animate-pulse rounded-[var(--radius-lg)] bg-bg-hover/60" />
                  <div className="h-4 animate-pulse rounded-[var(--radius-lg)] bg-bg-hover/60" />
                  <div className="h-40 animate-pulse rounded-[var(--radius-lg)] bg-bg-hover/60" />
                </div>
              ) : selectedJob ? (
                <JobDetail
                  job={selectedJob}
                  onClose={() => setSelectedJob(null)}
                />
              ) : null
            ) : (
              <div className="p-6">
                <StateBlock
                  tone="neutral"
                  icon={<Briefcase size={18} weight="bold" />}
                  title="Select a role"
                  description="Open a result to inspect the posting, score, and application entry point."
                />
              </div>
            )}
          </Surface>
        }
      />
    </div>
  );
}
