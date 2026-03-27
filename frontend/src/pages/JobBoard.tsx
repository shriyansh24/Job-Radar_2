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
import {
  MetricStrip,
  PageHeader,
  SplitWorkspace,
  StateBlock,
  Surface,
} from "../components/system";
import { cn } from "../lib/utils";
import { useDebounce } from "../hooks/useDebounce";
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
    <Surface
      tone="subtle"
      padding="md"
      interactive
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
      className={cn(
        "group transition-transform duration-150 hover:-translate-y-1 hover:-translate-x-1",
        selected && "border-[var(--color-accent-primary)] bg-[var(--color-accent-primary-subtle)]"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            {job.source ?? "source"}
          </div>
          <h3 className="mt-2 truncate font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
            {job.title}
          </h3>
          <p className="mt-1 truncate text-sm text-muted-foreground">
            {job.company_name ?? "Unknown company"}
          </p>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          {match ? <Badge variant="outline">{match}</Badge> : null}
          {job.is_starred ? <Star size={16} weight="fill" className="text-[var(--color-accent-warning)]" /> : null}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {job.location ? <Badge variant="secondary">{job.location}</Badge> : null}
        {job.remote_type ? <Badge variant="secondary">{job.remote_type}</Badge> : null}
        {job.job_type ? <Badge variant="secondary">{job.job_type}</Badge> : null}
        {job.experience_level ? <Badge variant="secondary">{job.experience_level}</Badge> : null}
      </div>
    </Surface>
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
        meta={
          <>
            <Badge variant="info">{total.toLocaleString()} results</Badge>
            <Badge variant="secondary">{activeFilterCount} active filters</Badge>
          </>
        }
        actions={
          <>
            <Button
              variant={searchMode === "exact" ? "primary" : "secondary"}
              onClick={() => setSearchMode("exact")}
              icon={<MagnifyingGlass size={16} weight="bold" />}
            >
              Exact
            </Button>
            <Button
              variant={searchMode === "semantic" ? "primary" : "secondary"}
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
      />

      <MetricStrip
        items={[
          {
            key: "mode",
            label: "Mode",
            value: searchMode === "semantic" ? "Semantic" : "Exact",
            icon: searchMode === "semantic" ? <Sparkle size={18} weight="bold" /> : <MagnifyingGlass size={18} weight="bold" />,
            tone: searchMode === "semantic" ? "warning" : "default",
            hint:
              searchMode === "semantic"
                ? "Best-match ranking without pagination."
                : "Filter-accurate results with page controls.",
          },
          {
            key: "results",
            label: "Results",
            value: total.toLocaleString(),
            icon: <Briefcase size={18} weight="bold" />,
            tone: "default",
            hint: "Current matches in the feed.",
          },
          {
            key: "page",
            label: "Page",
            value: searchMode === "semantic" ? "1" : `${currentPage}`,
            icon: <CaretRight size={18} weight="bold" />,
            tone: "default",
            hint: searchMode === "semantic" ? "Semantic search is unpaged." : "Exact search respects page state.",
          },
          {
            key: "filters",
            label: "Filters",
            value: activeFilterCount.toString(),
            icon: <Funnel size={18} weight="bold" />,
            tone: activeFilterCount > 0 ? "warning" : "default",
            hint: "Active refinements in the current query.",
          },
        ]}
      />

      <Surface tone="default" padding="md">
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
          <div className="mt-4 flex flex-wrap items-center gap-3 border-t-2 border-border pt-4">
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
            >
              Clear filters
            </Button>
            {searchMode === "semantic" ? (
              <Badge variant="secondary">Pagination disabled in semantic mode</Badge>
            ) : null}
          </div>
        ) : null}
      </Surface>

      <SplitWorkspace
        primary={
          <Surface tone="default" padding="none" className="overflow-hidden">
            <div className="flex items-center justify-between gap-3 border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
              <div>
                <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                  Results
                </div>
                <div className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
                  {searchMode === "semantic" ? "Semantic matches" : "Job list"}
                </div>
              </div>
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                {total.toLocaleString()} total
              </div>
            </div>

            <div className="max-h-[72vh] overflow-auto p-3 sm:p-4">
              {isError ? (
                <StateBlock
                  tone="danger"
                  title="Failed to load jobs"
                  description="Try again in a moment."
                />
              ) : isLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 8 }).map((_, index) => (
                    <div
                      key={index}
                      className="h-24 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]"
                    />
                  ))}
                </div>
              ) : jobs.length === 0 ? (
                <StateBlock
                  tone="muted"
                  title={searchMode === "semantic" ? "No semantic matches yet" : "No jobs found"}
                  description={
                    searchMode === "semantic"
                      ? "Try a broader description of the role, company, or stack."
                      : "Adjust the filters or search query to widen the feed."
                  }
                />
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
                <div className="flex items-center justify-between border-t-2 border-border px-5 py-4 sm:px-6">
                  <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Page <span className="text-foreground">{currentPage}</span> /{" "}
                    <span className="text-foreground">{totalPages}</span>
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={currentPage <= 1}
                      onClick={() => setFilters({ page: currentPage - 1 })}
                      icon={<CaretLeft size={14} weight="bold" />}
                    >
                      Prev
                    </Button>
                    <Button
                      variant="secondary"
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
          <Surface tone="default" padding="none" className="overflow-hidden xl:sticky xl:top-6">
            {selectedJobId ? (
              isLoadingDetail ? (
                <div className="space-y-4 p-5 sm:p-6">
                  <div className="h-10 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]" />
                  <div className="h-4 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]" />
                  <div className="h-40 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]" />
                </div>
              ) : selectedJob ? (
                <JobDetail job={selectedJob} onClose={() => setSelectedJob(null)} />
              ) : (
                <div className="p-5 sm:p-6">
                  <StateBlock
                    tone="muted"
                    title="Select a role"
                    description="Open a result to inspect the posting, score, and application entry point."
                    icon={<Briefcase size={16} weight="bold" />}
                  />
                </div>
              )
            ) : (
              <div className="p-5 sm:p-6">
                <StateBlock
                  tone="muted"
                  title="Select a role"
                  description="Open a result to inspect the posting, score, and application entry point."
                  icon={<Briefcase size={16} weight="bold" />}
                />
              </div>
            )}
          </Surface>
        }
      />
    </div>
  );
}
