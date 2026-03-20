import { Briefcase, CaretLeft, CaretRight } from "@phosphor-icons/react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { jobsApi, type JobListParams } from "../api/jobs";
import JobCard from "../components/jobs/JobCard";
import JobDetail from "../components/jobs/JobDetail";
import JobFilters from "../components/jobs/JobFilters";
import EmptyState from "../components/ui/EmptyState";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Skeleton from "../components/ui/Skeleton";
import { useDebounce } from "../hooks/useDebounce";
import { cn } from "../lib/utils";
import { useJobStore } from "../store/useJobStore";

function JobCardSkeleton() {
  return (
    <div className="p-4 border-b border-border/50 space-y-2">
      <Skeleton variant="text" className="w-3/4 h-5" />
      <Skeleton variant="text" className="w-1/2 h-4" />
      <div className="flex gap-2">
        <Skeleton variant="rect" className="w-16 h-5" />
        <Skeleton variant="rect" className="w-20 h-5" />
      </div>
    </div>
  );
}

export default function JobBoard() {
  const queryClient = useQueryClient();
  const { selectedJobId, filters, setSelectedJob, setFilters } = useJobStore();
  const [searchInput, setSearchInput] = useState(filters.q || '');
  const debouncedSearch = useDebounce(searchInput, 300);
  const [showFilters, setShowFilters] = useState(false);

  const activeFilters: JobListParams = {
    ...filters,
    q: debouncedSearch || undefined,
  };

  const { data, isLoading, isError } = useQuery({
    queryKey: ['jobs', activeFilters],
    queryFn: () => jobsApi.list(activeFilters).then((r) => r.data),
    placeholderData: keepPreviousData, // Keep old page data visible while new page loads
  });

  const { data: selectedJob, isLoading: isLoadingDetail } = useQuery({
    queryKey: ['job', selectedJobId],
    queryFn: () => jobsApi.get(selectedJobId!).then((r) => r.data),
    enabled: !!selectedJobId,
  });

  const starMutation = useMutation({
    mutationFn: ({ id, starred }: { id: string; starred: boolean }) =>
      jobsApi.update(id, { is_starred: starred }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      if (selectedJobId) queryClient.invalidateQueries({ queryKey: ['job', selectedJobId] });
    },
  });

  const jobs = data?.items || [];
  const totalPages = data?.total_pages || 0;
  const currentPage = filters.page || 1;

  return (
    <div className="flex flex-col min-h-0 gap-4">
      <JobFilters
        searchInput={searchInput}
        onSearchChange={setSearchInput}
        showFilters={showFilters}
        onToggleFilters={() => setShowFilters(!showFilters)}
        filters={filters}
        onFiltersChange={setFilters}
      />

      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-4">
        <Card
          padding="none"
          className={cn(
            "lg:col-span-5 overflow-hidden",
            selectedJobId ? "hidden lg:block" : "lg:col-span-12"
          )}
        >
          <div className="border-b border-border px-6 py-4 bg-bg-secondary/60 supports-[backdrop-filter]:bg-bg-secondary/40 backdrop-blur">
            <div className="flex items-baseline justify-between gap-3">
              <div>
                <div className="text-xs font-medium text-text-muted tracking-tight">
                  Results
                </div>
                <div className="mt-1 text-sm font-semibold text-text-primary">
                  Jobs
                </div>
              </div>
              <div className="text-xs text-text-muted">
                <span className="font-mono text-text-secondary">
                  {data?.total ?? 0}
                </span>{" "}
                total
              </div>
            </div>
          </div>

          <div className="flex-1 min-h-0 overflow-auto">
            {isError ? (
              <div className="p-8 text-center text-sm text-accent-danger">
                Failed to load jobs. Please try again.
              </div>
            ) : isLoading ? (
              Array.from({ length: 8 }).map((_, i) => <JobCardSkeleton key={i} />)
            ) : jobs.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  icon={<Briefcase size={40} weight="bold" />}
                  title="No jobs found"
                  description="Try adjusting your search or filters"
                />
              </div>
            ) : (
              jobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  isSelected={job.id === selectedJobId}
                  onClick={() => setSelectedJob(job.id)}
                  onToggleStar={() =>
                    starMutation.mutate({
                      id: job.id,
                      starred: !job.is_starred,
                    })
                  }
                />
              ))
            )}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-3 border-t border-border shrink-0">
              <span className="text-xs text-text-muted">
                Page{" "}
                <span className="font-mono text-text-secondary">
                  {currentPage}
                </span>{" "}
                /{" "}
                <span className="font-mono text-text-secondary">
                  {totalPages}
                </span>
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
          )}
        </Card>

        {selectedJobId ? (
          <Card padding="none" className="lg:col-span-7 overflow-hidden">
            <div className="flex-1 min-h-0 overflow-auto">
              {isLoadingDetail ? (
                <div className="p-8 space-y-4">
                  <Skeleton variant="text" className="w-3/4 h-6" />
                  <Skeleton variant="text" className="w-1/2 h-4" />
                  <Skeleton variant="rect" className="w-full h-40" />
                </div>
              ) : selectedJob ? (
                <JobDetail
                  job={selectedJob}
                  onClose={() => setSelectedJob(null)}
                />
              ) : null}
            </div>
          </Card>
        ) : null}
      </div>
    </div>
  );
}
