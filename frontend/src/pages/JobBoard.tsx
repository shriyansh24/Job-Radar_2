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
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import { cn } from "../lib/utils";
import { useDebounce } from "../hooks/useDebounce";
import { useJobStore } from "../store/useJobStore";
import { motion } from "framer-motion";

const HERO_PANEL =
  "border-2 border-[var(--color-text-primary)] bg-bg-secondary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";
const BUTTON_BASE =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !uppercase !tracking-[0.18em] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";

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

function scoreLabel(score: number | null) {
  if (score === null) return null;
  return `${Math.round(score * 100)}%`;
}

function JobRow({
  job,
  selected,
  onClick,
}: {
  job: Job;
  selected: boolean;
  onClick: () => void;
}) {
  const match = scoreLabel(job.match_score);

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "group w-full border-2 border-[var(--color-text-primary)] p-4 text-left shadow-[4px_4px_0px_0px_var(--color-text-primary)] transition-transform duration-150 hover:-translate-x-1 hover:-translate-y-1",
        selected ? "bg-accent-primary/8" : "bg-bg-secondary"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            {job.source ?? "source"}
          </div>
          <h3 className="mt-2 truncate text-lg font-semibold tracking-[-0.05em] text-text-primary">
            {job.title}
          </h3>
          <p className="mt-1 truncate text-sm text-text-secondary">
            {job.company_name ?? "Unknown company"}
          </p>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          {match ? (
            <span className={CHIP}>{match}</span>
          ) : null}
          {job.is_starred ? (
            <Star size={16} weight="fill" className="text-accent-warning" />
          ) : null}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {job.location ? <span className={CHIP}>{job.location}</span> : null}
        {job.remote_type ? <span className={CHIP}>{job.remote_type}</span> : null}
        {job.job_type ? <span className={CHIP}>{job.job_type}</span> : null}
        {job.experience_level ? <span className={CHIP}>{job.experience_level}</span> : null}
      </div>
    </button>
  );
}

function StatChip({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "primary" | "success";
}) {
  const toneClass = {
    default: "bg-bg-secondary",
    primary: "bg-accent-primary/8",
    success: "bg-accent-success/8",
  }[tone];

  return (
    <div className={cn("border-2 border-[var(--color-text-primary)] p-4", toneClass)}>
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-text-primary">
        {value}
      </div>
    </div>
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
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className={cn(HERO_PANEL, "overflow-hidden")}
      >
        <div className="grid gap-0 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.8fr)]">
          <div className="p-5 sm:p-6 lg:p-8">
            <div className="flex flex-wrap items-center gap-2">
              <span className={CHIP}>Discover</span>
              <span className={CHIP}>{total.toLocaleString()} results</span>
              <span className={CHIP}>{activeFilterCount} active filters</span>
            </div>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.06em] sm:text-5xl lg:text-6xl">
              Jobs
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              Search the feed with exact filters or semantic matching, then inspect the selected
              role in a live detail pane that stays usable on tablet and phone.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button
                variant={searchMode === "exact" ? "primary" : "secondary"}
                onClick={() => setSearchMode("exact")}
                icon={<MagnifyingGlass size={16} weight="bold" />}
                className={cn(
                  BUTTON_BASE,
                  searchMode === "exact"
                    ? "bg-accent-primary text-white"
                    : "bg-bg-secondary text-text-primary"
                )}
              >
                Exact
              </Button>
              <Button
                variant={searchMode === "semantic" ? "primary" : "secondary"}
                onClick={() => setSearchMode("semantic")}
                icon={<Sparkle size={16} weight="bold" />}
                className={cn(
                  BUTTON_BASE,
                  searchMode === "semantic"
                    ? "bg-accent-primary text-white"
                    : "bg-bg-secondary text-text-primary"
                )}
              >
                Semantic
              </Button>
              <Button
                variant="secondary"
                onClick={() => setShowFilters((current) => !current)}
                icon={<Funnel size={16} weight="bold" />}
                className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
              >
                Filters
              </Button>
            </div>
          </div>

          <div className="border-t-2 border-[var(--color-text-primary)] bg-bg-tertiary p-5 sm:p-6 xl:border-l-2 xl:border-t-0">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <StatChip
                label="Mode"
                value={searchMode === "semantic" ? "Semantic" : "Exact"}
                tone="primary"
              />
              <StatChip
                label="Page"
                value={searchMode === "semantic" ? "1" : `${currentPage}`}
              />
            </div>
            <p className="mt-4 text-sm leading-6 text-text-secondary">
              Semantic search ranks the best matches and ignores pagination. Exact mode honors the
              current filters and page state.
            </p>
          </div>
        </div>
      </motion.section>

      <div className={cn(HERO_PANEL, "p-5 sm:p-6")}>
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.35fr)_repeat(3,minmax(160px,1fr))]">
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
          <div className="mt-4 flex flex-wrap items-center gap-3 border-t-2 border-[var(--color-text-primary)] pt-4">
            <div className="min-w-[180px]">
              <Select
                options={sortOptions}
                value={filters.sort_by || "scraped_at"}
                onChange={(event) => setFilters({ sort_by: event.target.value, page: 1 })}
              />
            </div>
            <Button
              variant="secondary"
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
              className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
            >
              Clear filters
            </Button>
            {searchMode === "semantic" ? (
              <span className="text-xs text-text-muted">
                Semantic search ignores pagination and ranks the best matches first.
              </span>
            ) : null}
          </div>
        ) : null}
      </div>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
        <div className={cn(HERO_PANEL, "overflow-hidden")}>
          <div className="flex items-center justify-between gap-3 border-b-2 border-[var(--color-text-primary)] bg-bg-tertiary px-5 py-4 sm:px-6">
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                Results
              </div>
              <div className="mt-1 text-sm font-semibold uppercase tracking-[-0.04em] text-text-primary">
                {searchMode === "semantic" ? "Semantic matches" : "Job list"}
              </div>
            </div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-text-muted">
              {total.toLocaleString()} total
            </div>
          </div>

          <div className="max-h-[72vh] overflow-auto p-3 sm:p-4">
            {isError ? (
              <div className="border-2 border-[var(--color-text-primary)] bg-[var(--color-accent-danger)]/10 p-5">
                <div className="text-sm font-semibold uppercase tracking-[0.18em] text-accent-danger">
                  Failed to load jobs
                </div>
                <p className="mt-2 text-sm leading-6 text-text-secondary">
                  Try again in a moment.
                </p>
              </div>
            ) : isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 8 }).map((_, index) => (
                  <div
                    key={index}
                    className="h-24 animate-pulse border-2 border-[var(--color-text-primary)] bg-bg-tertiary"
                  />
                ))}
              </div>
            ) : jobs.length === 0 ? (
              <div className="border-2 border-[var(--color-text-primary)] bg-bg-tertiary p-5">
                <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-text-muted">
                  <Briefcase size={16} weight="bold" />
                  {searchMode === "semantic" ? "No semantic matches yet" : "No jobs found"}
                </div>
                <p className="mt-3 text-sm leading-6 text-text-secondary">
                  {searchMode === "semantic"
                    ? "Try a broader description of the role, company, or stack."
                    : "Adjust the filters or search query to widen the feed."}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
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
              <div className="flex items-center justify-between border-t-2 border-[var(--color-text-primary)] px-5 py-4 sm:px-6">
                <span className="text-xs font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Page <span className="text-text-primary">{currentPage}</span> /{" "}
                  <span className="text-text-primary">{totalPages}</span>
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={currentPage <= 1}
                    onClick={() => setFilters({ page: currentPage - 1 })}
                    icon={<CaretLeft size={14} weight="bold" />}
                    className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
                  >
                    Prev
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={currentPage >= totalPages}
                    onClick={() => setFilters({ page: currentPage + 1 })}
                    icon={<CaretRight size={14} weight="bold" />}
                    className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
                  >
                    Next
                  </Button>
                </div>
              </div>
            ) : null
          ) : null}
        </div>

        <div className="xl:sticky xl:top-6">
          <div className={cn(HERO_PANEL, "overflow-hidden")}>
            {selectedJobId ? (
              isLoadingDetail ? (
                <div className="space-y-4 p-5 sm:p-6">
                  <div className="h-10 animate-pulse border-2 border-[var(--color-text-primary)] bg-bg-tertiary" />
                  <div className="h-4 animate-pulse border-2 border-[var(--color-text-primary)] bg-bg-tertiary" />
                  <div className="h-40 animate-pulse border-2 border-[var(--color-text-primary)] bg-bg-tertiary" />
                </div>
              ) : selectedJob ? (
                <JobDetail job={selectedJob} onClose={() => setSelectedJob(null)} />
              ) : null
            ) : (
              <div className="p-5 sm:p-6">
                <div className="border-2 border-[var(--color-text-primary)] bg-bg-tertiary p-5">
                  <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-text-muted">
                    <Briefcase size={16} weight="bold" />
                    Select a role
                  </div>
                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    Open a result to inspect the posting, score, and application entry point.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
