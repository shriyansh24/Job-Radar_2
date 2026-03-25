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
import Button from "../ui/Button";
import Modal from "../ui/Modal";
import { toast } from "../ui/toastService";

interface JobDetailProps {
  job: Job;
  onClose: () => void;
}

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-bg-secondary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const INSET =
  "border-2 border-[var(--color-text-primary)] bg-bg-tertiary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";
const BUTTON_BASE =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !uppercase !tracking-[0.18em] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";

function ScoreCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className={cn(INSET, "p-4")}>
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
        {label}
      </div>
      <div className="mt-3 text-3xl font-semibold tracking-[-0.06em] text-text-primary">
        {value}
      </div>
      <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
    </div>
  );
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

  const matchScore = job.match_score !== null ? `${Math.round(job.match_score * 100)}%` : null;
  const tfidfScore = job.tfidf_score !== null ? job.tfidf_score.toFixed(3) : null;

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="flex items-start justify-between gap-4 border-b-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] p-5 sm:p-6">
        <div className="flex min-w-0 gap-3">
          {job.company_logo_url ? (
            <img
              src={job.company_logo_url}
              alt=""
              className="size-12 shrink-0 border-2 border-[var(--color-text-primary)] object-cover"
            />
          ) : (
            <div className="flex size-12 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]">
              <Briefcase size={18} weight="bold" />
            </div>
          )}
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className={CHIP}>{job.source ?? "source"}</span>
              {job.remote_type ? <span className={CHIP}>{job.remote_type}</span> : null}
              {job.is_enriched ? <span className={CHIP}>Enriched</span> : null}
            </div>
            <h2 className="mt-3 truncate text-2xl font-semibold tracking-[-0.06em] text-text-primary sm:text-3xl">
              {job.title}
            </h2>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-text-secondary">
              {job.company_name && <span>{job.company_name}</span>}
              {job.location && (
                <>
                  <span className="text-text-muted">•</span>
                  <span className="flex items-center gap-1">
                    <MapPin size={12} weight="bold" />
                    {job.location}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="inline-flex size-10 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] text-text-muted transition-colors hover:bg-[var(--color-accent-primary)]/8 hover:text-text-primary lg:hidden"
          aria-label="Close detail pane"
        >
          <X size={18} weight="bold" />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-auto p-5 sm:p-6">
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {job.experience_level ? <span className={CHIP}>{job.experience_level}</span> : null}
            {job.job_type ? <span className={CHIP}>{job.job_type}</span> : null}
            {job.remote_type ? <span className={CHIP}>{job.remote_type}</span> : null}
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {matchScore ? (
              <ScoreCard
                label="Match score"
                value={matchScore}
                hint="Overall fit signal for this role."
              />
            ) : (
              <ScoreCard
                label="Match score"
                value="—"
                hint="No ranking score has been calculated yet."
              />
            )}
            <ScoreCard
              label="TF-IDF"
              value={tfidfScore ?? "—"}
              hint="Text relevance against the current profile."
            />
            <ScoreCard
              label="Salary"
              value={
                job.salary_min || job.salary_max
                  ? job.salary_min && job.salary_max
                    ? `$${(job.salary_min / 1000).toFixed(0)}k-$${(job.salary_max / 1000).toFixed(0)}k`
                    : job.salary_min
                      ? `$${(job.salary_min / 1000).toFixed(0)}k+`
                      : `Up to $${(job.salary_max! / 1000).toFixed(0)}k`
                  : "—"
              }
              hint={job.salary_period ? `Per ${job.salary_period}` : "No salary range recorded."}
            />
          </div>

          {job.summary_ai ? (
            <div className={cn(INSET, "p-4")}>
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-text-muted">
                <Sparkle size={14} weight="fill" className="text-accent-primary" />
                AI Summary
              </div>
              <p className="mt-3 text-sm leading-7 text-text-primary">{job.summary_ai}</p>
            </div>
          ) : null}

          {job.skills_required.length > 0 ? (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                Required skills
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {job.skills_required.map((skill) => (
                  <span key={skill} className={CHIP}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {job.skills_nice_to_have.length > 0 ? (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                Nice to have
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {job.skills_nice_to_have.map((skill) => (
                  <span key={skill} className={CHIP}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {job.tech_stack.length > 0 ? (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                Tech stack
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {job.tech_stack.map((tech) => (
                  <span key={tech} className={cn(CHIP, "bg-bg-tertiary")}>
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {job.green_flags.length > 0 ? (
            <div className={cn(PANEL, "p-4")}>
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-text-muted">
                <CheckCircle size={14} weight="fill" className="text-accent-success" />
                Green flags
              </div>
              <ul className="mt-3 space-y-2">
                {job.green_flags.map((flag, index) => (
                  <li key={`${flag}-${index}`} className="flex items-start gap-2 text-sm leading-6 text-text-secondary">
                    <span className="mt-1 inline-flex size-3 shrink-0 border border-[var(--color-text-primary)] bg-accent-success/30" />
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {job.red_flags.length > 0 ? (
            <div className={cn(PANEL, "p-4")}>
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-text-muted">
                <Warning size={14} weight="fill" className="text-accent-danger" />
                Red flags
              </div>
              <ul className="mt-3 space-y-2">
                {job.red_flags.map((flag, index) => (
                  <li key={`${flag}-${index}`} className="flex items-start gap-2 text-sm leading-6 text-text-secondary">
                    <span className="mt-1 inline-flex size-3 shrink-0 border border-[var(--color-text-primary)] bg-accent-danger/30" />
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {job.description_markdown ? (
            <div className={cn(PANEL, "p-4")}>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                Description
              </div>
              <div
                className={cn(
                  "prose prose-sm max-w-none text-text-primary",
                  "[&_a]:text-accent-primary [&_strong]:text-text-primary [&_h1]:text-text-primary [&_h2]:text-text-primary [&_h3]:text-text-primary"
                )}
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {job.description_markdown}
                </ReactMarkdown>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="border-t-2 border-[var(--color-text-primary)] bg-bg-tertiary p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="primary"
            onClick={() => setShowApplyModal(true)}
            icon={<Briefcase size={14} weight="bold" />}
            className={cn(BUTTON_BASE, "bg-accent-primary text-white")}
          >
            Apply
          </Button>
          {safeSourceUrl ? (
            <Button
              variant="secondary"
              onClick={() => window.open(safeSourceUrl, "_blank", "noopener,noreferrer")}
              icon={<LinkSimple size={14} weight="bold" />}
              className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
            >
              Original
            </Button>
          ) : null}
        </div>
      </div>

      <Modal
        open={showApplyModal}
        onClose={() => setShowApplyModal(false)}
        title="Create Application"
        size="sm"
        className="!rounded-none !border-2 !border-[var(--color-text-primary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]"
      >
        <div className="space-y-4">
          <p className="text-sm leading-6 text-text-secondary">
            Track your application for <strong className="text-text-primary">{job.title}</strong>{" "}
            at <strong className="text-text-primary">{job.company_name}</strong>?
          </p>
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => setShowApplyModal(false)}
              className={cn(BUTTON_BASE, "bg-bg-secondary text-text-primary")}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              loading={applyMutation.isPending}
              onClick={() => applyMutation.mutate()}
              className={cn(BUTTON_BASE, "bg-accent-primary text-white")}
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
