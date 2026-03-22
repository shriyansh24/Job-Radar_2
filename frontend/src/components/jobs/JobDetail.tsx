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
import { cn } from "../../lib/utils";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Card from "../ui/Card";
import Modal from "../ui/Modal";
import { toast } from "../ui/toastService";
import ScoreGauge from "./ScoreGauge";

interface JobDetailProps {
  job: Job;
  onClose: () => void;
}

export default function JobDetail({ job, onClose }: JobDetailProps) {
  const queryClient = useQueryClient();
  const [showApplyModal, setShowApplyModal] = useState(false);

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

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          {job.company_logo_url && (
            <img src={job.company_logo_url} alt="" className="w-10 h-10 rounded-[var(--radius-md)] object-cover" />
          )}
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-text-primary truncate">{job.title}</h2>
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              {job.company_name && <span>{job.company_name}</span>}
              {job.location && (
                <>
                  <span className="text-text-muted">&middot;</span>
                  <span className="flex items-center gap-1">
                    <MapPin size={12} weight="bold" />
                    {job.location}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        <button onClick={onClose} className="p-2 rounded-[var(--radius-md)] hover:bg-bg-tertiary text-text-muted lg:hidden">
          <X size={18} weight="bold" />
        </button>
      </div>

      <div className="flex-1 overflow-auto px-6 py-4 space-y-6">
        <div className="flex flex-wrap gap-2">
          {job.remote_type && <Badge variant="info">{job.remote_type}</Badge>}
          {job.experience_level && <Badge>{job.experience_level}</Badge>}
          {job.job_type && <Badge>{job.job_type}</Badge>}
          {job.is_enriched && <Badge variant="success">Enriched</Badge>}
        </div>

        <div className="grid grid-cols-2 gap-3">
          {job.match_score !== null && (
            <Card padding="sm">
              <ScoreGauge score={job.match_score} label="Match Score" />
            </Card>
          )}
          {job.tfidf_score !== null && (
            <Card padding="sm">
              <p className="text-xs text-text-muted mb-1">TF-IDF Score</p>
              <p className="text-sm font-medium text-text-primary">{job.tfidf_score.toFixed(3)}</p>
            </Card>
          )}
        </div>

        {(job.salary_min || job.salary_max) && (
          <Card padding="sm">
            <p className="text-xs text-text-muted mb-1">Salary Range</p>
            <p className="text-lg font-semibold text-accent-success">
              {job.salary_min && job.salary_max
                ? `$${(job.salary_min / 1000).toFixed(0)}k - $${(job.salary_max / 1000).toFixed(0)}k`
                : job.salary_min
                ? `$${(job.salary_min / 1000).toFixed(0)}k+`
                : `Up to $${(job.salary_max! / 1000).toFixed(0)}k`}
              {job.salary_period && <span className="text-sm text-text-muted ml-1">/{job.salary_period}</span>}
            </p>
          </Card>
        )}

        {job.summary_ai && (
          <div>
            <h3 className="text-sm font-medium text-text-secondary flex items-center gap-1.5 mb-2">
              <Sparkle size={14} weight="fill" className="text-accent-primary" />
              AI Summary
            </h3>
            <p className="text-sm text-text-primary leading-relaxed">{job.summary_ai}</p>
          </div>
        )}

        {job.skills_required.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-text-secondary mb-2">Required Skills</h3>
            <div className="flex flex-wrap gap-1.5">
              {job.skills_required.map((s) => (
                <Badge key={s} variant="info" size="sm">{s}</Badge>
              ))}
            </div>
          </div>
        )}
        {job.skills_nice_to_have.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-text-secondary mb-2">Nice to Have</h3>
            <div className="flex flex-wrap gap-1.5">
              {job.skills_nice_to_have.map((s) => (
                <Badge key={s} size="sm">{s}</Badge>
              ))}
            </div>
          </div>
        )}
        {job.tech_stack.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-text-secondary mb-2">Tech Stack</h3>
            <div className="flex flex-wrap gap-1.5">
              {job.tech_stack.map((s) => (
                <Badge key={s} variant="info" size="sm">{s}</Badge>
              ))}
            </div>
          </div>
        )}

        {job.green_flags.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-text-secondary flex items-center gap-1.5 mb-2">
              <CheckCircle size={14} weight="fill" className="text-accent-success" />
              Green Flags
            </h3>
            <ul className="space-y-1">
              {job.green_flags.map((f, i) => (
                <li key={i} className="text-sm text-accent-success flex items-start gap-2">
                  <CheckCircle size={12} weight="fill" className="mt-1 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}
        {job.red_flags.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-text-secondary flex items-center gap-1.5 mb-2">
              <Warning size={14} weight="fill" className="text-accent-danger" />
              Red Flags
            </h3>
            <ul className="space-y-1">
              {job.red_flags.map((f, i) => (
                <li key={i} className="text-sm text-accent-danger flex items-start gap-2">
                  <Warning size={12} weight="fill" className="mt-1 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}

        {job.description_markdown && (
          <div>
            <h3 className="text-sm font-medium text-text-secondary mb-2">Description</h3>
            <div className={cn(
              'prose prose-sm prose-invert max-w-none text-text-primary',
              '[&_a]:text-accent-primary [&_h1]:text-text-primary [&_h2]:text-text-primary [&_h3]:text-text-primary [&_strong]:text-text-primary [&_li]:text-text-secondary'
            )}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {job.description_markdown}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>

      <div className="px-6 py-3 border-t border-border flex items-center gap-2 shrink-0">
        <Button
          variant="primary"
          onClick={() => setShowApplyModal(true)}
          icon={<Briefcase size={14} weight="bold" />}
        >
          Apply
        </Button>
        {job.source_url && (
          <Button
            variant="secondary"
            onClick={() => window.open(job.source_url!, "_blank")}
            icon={<LinkSimple size={14} weight="bold" />}
          >
            Original
          </Button>
        )}
      </div>

      <Modal open={showApplyModal} onClose={() => setShowApplyModal(false)} title="Create Application" size="sm">
        <p className="text-sm text-text-secondary mb-4">
          Track your application for <strong className="text-text-primary">{job.title}</strong> at{' '}
          <strong className="text-text-primary">{job.company_name}</strong>?
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setShowApplyModal(false)}>Cancel</Button>
          <Button variant="primary" loading={applyMutation.isPending} onClick={() => applyMutation.mutate()}>
            Create
          </Button>
        </div>
      </Modal>
    </div>
  );
}
