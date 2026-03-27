import {
  Briefcase,
  CheckCircle,
  LinkSimple,
  MapPin,
  Sparkle,
  Warning,
  X,
} from "@phosphor-icons/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { useState } from "react";
import remarkGfm from "remark-gfm";
import type { Job } from "../../api/jobs";
import { pipelineApi } from "../../api/pipeline";
import { cn, getSafeExternalUrl } from "../../lib/utils";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Modal from "../ui/Modal";
import {
  MetricStrip,
  StateBlock,
  Surface,
} from "../system";
import { toast } from "../ui/toastService";

interface JobDetailProps {
  job: Job;
  onClose: () => void;
}

function formatSalary(job: Job) {
  if (job.salary_min || job.salary_max) {
    if (job.salary_min && job.salary_max) {
      return `$${(job.salary_min / 1000).toFixed(0)}k-$${(job.salary_max / 1000).toFixed(0)}k`;
    }

    if (job.salary_min) {
      return `$${(job.salary_min / 1000).toFixed(0)}k+`;
    }

    return `Up to $${(job.salary_max! / 1000).toFixed(0)}k`;
  }

  return "—";
}

export default function JobDetail({ job, onClose }: JobDetailProps) {
  const queryClient = useQueryClient();
  const [showApplyModal, setShowApplyModal] = useState(false);
  const safeSourceUrl = getSafeExternalUrl(job.source_url);

  const applyMutation = useMutation({
    mutationFn: () =>
      pipelineApi.create({
        job_id: job.id,
        company_name: job.company_name || "Unknown",
        position_title: job.title,
        source: job.source,
      }),
    onSuccess: () => {
      toast("success", "Application created");
      setShowApplyModal(false);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: () => toast("error", "Failed to create application"),
  });

  const matchScore = job.match_score !== null ? `${Math.round(job.match_score * 100)}%` : "—";
  const tfidfScore = job.tfidf_score !== null ? job.tfidf_score.toFixed(3) : "—";

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="flex items-start justify-between gap-4 border-b-2 border-border bg-[var(--color-bg-tertiary)] p-5 sm:p-6">
        <div className="flex min-w-0 gap-3">
          {job.company_logo_url ? (
            <img
              src={job.company_logo_url}
              alt=""
              className="size-12 shrink-0 border-2 border-border object-cover shadow-[var(--shadow-xs)]"
            />
          ) : (
            <div className="flex size-12 shrink-0 items-center justify-center border-2 border-border bg-background text-muted-foreground shadow-[var(--shadow-xs)]">
              <Briefcase size={18} weight="bold" />
            </div>
          )}
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">{job.source ?? "source"}</Badge>
              {job.remote_type ? <Badge variant="secondary">{job.remote_type}</Badge> : null}
              {job.is_enriched ? <Badge variant="info">Enriched</Badge> : null}
            </div>
            <h2 className="mt-3 truncate font-display text-2xl font-black uppercase tracking-[-0.06em] text-foreground sm:text-3xl">
              {job.title}
            </h2>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              {job.company_name ? <span>{job.company_name}</span> : null}
              {job.location ? (
                <>
                  <span className="text-text-muted">•</span>
                  <span className="flex items-center gap-1">
                    <MapPin size={12} weight="bold" />
                    {job.location}
                  </span>
                </>
              ) : null}
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="inline-flex size-10 shrink-0 items-center justify-center border-2 border-border bg-background text-text-muted transition-colors hover:bg-[var(--color-accent-primary-subtle)] hover:text-foreground lg:hidden"
          aria-label="Close detail pane"
        >
          <X size={18} weight="bold" />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-auto p-5 sm:p-6">
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {job.experience_level ? <Badge variant="outline">{job.experience_level}</Badge> : null}
            {job.job_type ? <Badge variant="outline">{job.job_type}</Badge> : null}
            {job.remote_type ? <Badge variant="outline">{job.remote_type}</Badge> : null}
          </div>

          <MetricStrip
            items={[
              {
                key: "match",
                label: "Match score",
                value: matchScore,
                hint: "Overall fit signal for this role.",
                icon: <Sparkle size={18} weight="bold" />,
                tone: job.match_score ? "success" : "default",
              },
              {
                key: "tfidf",
                label: "TF-IDF",
                value: tfidfScore,
                hint: "Text relevance against the current profile.",
                icon: <CheckCircle size={18} weight="bold" />,
                tone: "default",
              },
              {
                key: "salary",
                label: "Salary",
                value: formatSalary(job),
                hint: job.salary_period ? `Per ${job.salary_period}` : "No salary range recorded.",
                icon: <Briefcase size={18} weight="bold" />,
                tone: job.salary_min || job.salary_max ? "warning" : "default",
              },
            ]}
            className="grid-cols-1 md:grid-cols-3"
          />

          {job.summary_ai ? (
            <StateBlock
              tone="muted"
              title="AI summary"
              description={job.summary_ai}
              icon={<Sparkle size={14} weight="fill" />}
            />
          ) : null}

          {job.skills_required.length > 0 ? (
            <Surface tone="subtle" padding="md">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Required skills
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {job.skills_required.map((skill) => (
                  <Badge key={skill} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            </Surface>
          ) : null}

          {job.skills_nice_to_have.length > 0 ? (
            <Surface tone="subtle" padding="md">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Nice to have
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {job.skills_nice_to_have.map((skill) => (
                  <Badge key={skill} variant="outline">
                    {skill}
                  </Badge>
                ))}
              </div>
            </Surface>
          ) : null}

          {job.tech_stack.length > 0 ? (
            <Surface tone="subtle" padding="md">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Tech stack
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {job.tech_stack.map((tech) => (
                  <Badge key={tech} variant="default">
                    {tech}
                  </Badge>
                ))}
              </div>
            </Surface>
          ) : null}

          {job.green_flags.length > 0 ? (
            <StateBlock
              tone="success"
              title="Green flags"
              description={
                <ul className="space-y-2">
                  {job.green_flags.map((flag, index) => (
                    <li key={`${flag}-${index}`} className="flex items-start gap-2 text-sm leading-6">
                      <span className="mt-1 inline-flex size-3 shrink-0 border border-border bg-[var(--color-accent-success)]/30" />
                      {flag}
                    </li>
                  ))}
                </ul>
              }
              icon={<CheckCircle size={14} weight="fill" className="text-[var(--color-accent-success)]" />}
            />
          ) : null}

          {job.red_flags.length > 0 ? (
            <StateBlock
              tone="danger"
              title="Red flags"
              description={
                <ul className="space-y-2">
                  {job.red_flags.map((flag, index) => (
                    <li key={`${flag}-${index}`} className="flex items-start gap-2 text-sm leading-6">
                      <span className="mt-1 inline-flex size-3 shrink-0 border border-border bg-[var(--color-accent-danger)]/30" />
                      {flag}
                    </li>
                  ))}
                </ul>
              }
              icon={<Warning size={14} weight="fill" className="text-[var(--color-accent-danger)]" />}
            />
          ) : null}

          {job.description_markdown ? (
            <Surface tone="default" padding="md">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Description
              </div>
              <div
                className={cn(
                  "prose prose-sm mt-3 max-w-none text-foreground",
                  "[&_a]:text-[var(--color-accent-primary)] [&_strong]:text-foreground [&_h1]:text-foreground [&_h2]:text-foreground [&_h3]:text-foreground"
                )}
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{job.description_markdown}</ReactMarkdown>
              </div>
            </Surface>
          ) : null}
        </div>
      </div>

      <div className="border-t-2 border-border bg-[var(--color-bg-tertiary)] p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="primary"
            onClick={() => setShowApplyModal(true)}
            icon={<Briefcase size={14} weight="bold" />}
          >
            Apply
          </Button>
          {safeSourceUrl ? (
            <Button
              variant="secondary"
              onClick={() => window.open(safeSourceUrl, "_blank", "noopener,noreferrer")}
              icon={<LinkSimple size={14} weight="bold" />}
            >
              Original
            </Button>
          ) : null}
        </div>
      </div>

      <Modal open={showApplyModal} onClose={() => setShowApplyModal(false)} title="Create Application" size="sm">
        <div className="space-y-4">
          <p className="text-sm leading-6 text-muted-foreground">
            Track your application for <strong className="text-foreground">{job.title}</strong>{" "}
            at <strong className="text-foreground">{job.company_name}</strong>?
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowApplyModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" loading={applyMutation.isPending} onClick={() => applyMutation.mutate()}>
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
