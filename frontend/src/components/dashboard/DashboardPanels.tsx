import {
  ArrowRight,
  Buildings,
  PaperPlaneTilt,
  Plus,
} from "@phosphor-icons/react";
import { formatDistanceToNow } from "date-fns";
import { motion } from "framer-motion";
import type { ReactNode } from "react";
import type { Job } from "../../api/jobs";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";

export function FeedRow({
  title,
  meta,
  badge,
  icon,
}: {
  title: string;
  meta: string;
  badge?: string;
  icon: ReactNode;
}) {
  return (
    <Surface tone="subtle" padding="md" className="transition-transform duration-150 hover:-translate-y-0.5">
      <div className="flex items-start gap-4">
        <div className="flex size-11 shrink-0 items-center justify-center border-2 border-border bg-background text-muted-foreground">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-[-0.03em] text-foreground sm:text-base">
              {title}
            </h3>
            {badge ? <Badge variant="outline">{badge}</Badge> : null}
          </div>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{meta}</p>
        </div>
      </div>
    </Surface>
  );
}

export function PipelineSummaryPanel({
  totalApps,
  lateStageCount,
  totalOffers,
}: {
  totalApps: number;
  lateStageCount: number;
  totalOffers: number;
}) {
  return (
    <Surface tone="default" padding="none" className="overflow-hidden">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">Pipeline</div>
          <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground sm:text-2xl">
            Stage mix
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">Applied</Badge>
          <Badge variant="secondary">Interview</Badge>
          <Badge variant="secondary">Offer</Badge>
        </div>
      </div>

      <div className="space-y-5 p-5 sm:p-6">
        <div className="relative h-12 overflow-hidden border-2 border-border bg-background">
          <motion.div
            className="h-full bg-[var(--color-text-primary)]"
            initial={{ width: 0 }}
            animate={{ width: totalApps > 0 ? "55%" : "0%" }}
            transition={{ type: "spring", stiffness: 180, damping: 24 }}
          />
          <motion.div
            className="h-full bg-[var(--color-accent-primary)]"
            initial={{ width: 0 }}
            animate={{ width: totalApps > 0 ? "30%" : "0%" }}
            transition={{ type: "spring", stiffness: 180, damping: 24, delay: 0.05 }}
          />
          <motion.div
            className="h-full bg-[var(--color-accent-success)]"
            initial={{ width: 0 }}
            animate={{ width: totalApps > 0 ? "15%" : "0%" }}
            transition={{ type: "spring", stiffness: 180, damping: 24, delay: 0.1 }}
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <StateBlock
            tone="muted"
            title="Top of funnel"
            description={`${Math.max(totalApps - lateStageCount, 0)} applications are still in early stages.`}
          />
          <StateBlock
            tone="warning"
            title="Late stage"
            description={`${lateStageCount.toLocaleString()} applications are in interviews or beyond.`}
          />
          <StateBlock
            tone="success"
            title="Offers"
            description={`${totalOffers.toLocaleString()} offers are currently open.`}
          />
        </div>
      </div>
    </Surface>
  );
}

export function JobFeedPanel({
  jobs,
  loadingJobs,
}: {
  jobs: Job[] | undefined;
  loadingJobs: boolean;
}) {
  return (
    <Surface tone="default" padding="none" className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">Feed</div>
          <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
            Recent jobs
          </h2>
        </div>
        <Badge variant="info">Live</Badge>
      </div>

      <div className="space-y-3 p-5 sm:p-6">
        {loadingJobs ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="h-20 animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]" />
            ))}
          </div>
        ) : jobs?.length ? (
          jobs.map((job, index) => {
            const jobMeta = [
              job.location,
              job.remote_type,
              job.posted_at ? formatDistanceToNow(new Date(job.posted_at), { addSuffix: true }) : null,
            ]
              .filter(Boolean)
              .join(" · ");

            return (
              <FeedRow
                key={job.id}
                title={`${job.title}${job.company_name ? ` @ ${job.company_name}` : ""}`}
                meta={jobMeta}
                badge={job.match_score !== null ? `${Math.round(job.match_score * 100)}% match` : undefined}
                icon={index === 0 ? <PaperPlaneTilt size={18} weight="bold" /> : <Buildings size={18} weight="bold" />}
              />
            );
          })
        ) : (
          <StateBlock tone="muted" title="No recent jobs yet" description="New jobs will appear here." />
        )}
      </div>
    </Surface>
  );
}

export function NextActionsPanel({
  lateStageCount,
  firstJob,
}: {
  lateStageCount: number;
  firstJob: Job | undefined;
}) {
  return (
    <Surface tone="default" padding="none" className="overflow-hidden">
      <div className="flex items-end justify-between gap-4 border-b-2 border-border bg-[var(--color-bg-tertiary)] px-5 py-4 sm:px-6">
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">Next</div>
          <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground sm:text-2xl">
            Queue
          </h2>
        </div>
      </div>

      <div className="space-y-3 p-5 sm:p-6">
        <StateBlock
          tone={lateStageCount > 0 ? "warning" : "muted"}
          title={lateStageCount > 0 ? `${lateStageCount} need review` : "No urgent follow-up"}
          description={
            lateStageCount > 0
              ? "Review interviews and offers."
              : "No interview or offer records need attention."
          }
          action={<Badge variant={lateStageCount > 0 ? "warning" : "secondary"}>{lateStageCount > 0 ? "Urgent" : "Clear"}</Badge>}
        />
        <StateBlock
          tone={firstJob ? "warning" : "muted"}
          title={firstJob ? "Newest posting" : "No posting to review"}
          description={
            firstJob
              ? `${firstJob.title}${firstJob.location ? ` · ${firstJob.location}` : ""}`
              : "No new posting in the queue."
          }
          action={<Badge variant={firstJob ? "info" : "secondary"}>{firstJob ? "New" : "Empty"}</Badge>}
        />
        <StateBlock tone="muted" title="Queue clear" description="No other actions are pending." />
      </div>
    </Surface>
  );
}

export function DashboardHeaderActions({
  onBrowseJobs,
  onAddApplication,
}: {
  onBrowseJobs: () => void;
  onAddApplication: () => void;
}) {
  return (
    <>
      <Button variant="primary" icon={<ArrowRight size={16} weight="bold" />} onClick={onBrowseJobs}>
        Browse jobs
      </Button>
      <Button variant="secondary" icon={<Plus size={16} weight="bold" />} onClick={onAddApplication}>
        Add application
      </Button>
    </>
  );
}
