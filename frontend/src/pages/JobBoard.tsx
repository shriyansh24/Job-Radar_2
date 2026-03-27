import { Briefcase, Funnel, MagnifyingGlass, Sparkle } from "@phosphor-icons/react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { jobsApi, type JobListParams } from "../api/jobs";
import { useDebounce } from "../hooks/useDebounce";
import { MetricStrip, PageHeader, SplitWorkspace } from "../components/system";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import { JobBoardFilters } from "../components/jobs/JobBoardFilters";
import { JobDetailPanel } from "../components/jobs/JobDetailPanel";
import { JobResultsPanel } from "../components/jobs/JobResultsPanel";
import { useJobStore } from "../store/useJobStore";
import { type SearchMode } from "../components/jobs/jobBoardUtils";
import { Surface } from "../components/system/Surface";

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
        description="Search, filter, and inspect the feed."
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
            icon:
              searchMode === "semantic" ? (
                <Sparkle size={18} weight="bold" />
              ) : (
                <MagnifyingGlass size={18} weight="bold" />
              ),
            tone: searchMode === "semantic" ? "warning" : "default",
            hint: searchMode === "semantic" ? "Relevance-ranked results." : "Paged filter results.",
          },
          {
            key: "results",
            label: "Results",
            value: total.toLocaleString(),
            icon: <Briefcase size={18} weight="bold" />,
            tone: "default",
            hint: "Jobs returned.",
          },
          {
            key: "page",
            label: "Page",
            value: searchMode === "semantic" ? "1" : `${currentPage}`,
            icon: <Briefcase size={18} weight="bold" />,
            tone: "default",
            hint: searchMode === "semantic" ? "Single list." : "Current page.",
          },
          {
            key: "filters",
            label: "Filters",
            value: activeFilterCount.toString(),
            icon: <Funnel size={18} weight="bold" />,
            tone: activeFilterCount > 0 ? "warning" : "default",
            hint: "Applied filters.",
          },
        ]}
      />

      <Surface tone="default" padding="md">
        <JobBoardFilters
          searchMode={searchMode}
          searchInput={searchInput}
          onSearchChange={(value) => {
            setSearchInput(value);
            setFilters({ q: value, page: 1 });
          }}
          showFilters={showFilters}
          filters={filters}
          onFiltersChange={(nextFilters) => setFilters({ ...nextFilters, page: 1 })}
          onClearFilters={() => {
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
        />
      </Surface>

      <SplitWorkspace
        primary={
          <JobResultsPanel
            searchMode={searchMode}
            jobs={jobs}
            total={total}
            isLoading={isLoading}
            isError={isError}
            selectedJobId={selectedJobId}
            onSelectJob={(jobId) => setSelectedJob(jobId)}
            currentPage={currentPage}
            totalPages={totalPages}
            onPrevPage={() => setFilters({ page: currentPage - 1 })}
            onNextPage={() => setFilters({ page: currentPage + 1 })}
          />
        }
        secondary={
          <JobDetailPanel
            selectedJobId={selectedJobId}
            isLoadingDetail={isLoadingDetail}
            selectedJob={selectedJob ?? null}
            onClose={() => setSelectedJob(null)}
          />
        }
      />
    </div>
  );
}
