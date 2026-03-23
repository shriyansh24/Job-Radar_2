import {
  Buildings,
  Clock,
  MapPin,
  Monitor,
  Star,
} from "@phosphor-icons/react";
import { formatDistanceToNow } from "date-fns";
import type { Job } from "../../api/jobs";
import { cn } from "../../lib/utils";
import Badge from "../ui/Badge";
import FreshnessBadge from "./FreshnessBadge";

function MatchScoreBadge({ score }: { score: number | null }) {
  if (score === null) return null;
  const pct = Math.round(score * 100);
  const variant = pct >= 80 ? "success" : pct >= 50 ? "warning" : "danger";
  return <Badge variant={variant}>{pct}%</Badge>;
}

function SalaryRange({ min, max, period }: { min: number | null; max: number | null; period: string | null }) {
  if (!min && !max) return null;
  const fmt = (n: number) => n >= 1000 ? `$${(n / 1000).toFixed(0)}k` : `$${n}`;
  return (
    <span className="text-xs text-accent-success font-mono">
      {min && max ? `${fmt(min)} - ${fmt(max)}` : min ? `${fmt(min)}+` : `Up to ${fmt(max!)}`}
      {period && <span className="text-text-muted">/{period}</span>}
    </span>
  );
}

interface JobCardProps {
  job: Job;
  isSelected: boolean;
  onClick: () => void;
  onToggleStar: () => void;
}

export default function JobCard({ job, isSelected, onClick, onToggleStar }: JobCardProps) {
  return (
    <div
      className={cn(
        "px-6 py-4 border-b border-border/50 cursor-pointer transition-[background-color,transform] duration-[var(--transition-fast)]",
        isSelected
          ? "bg-bg-tertiary border-l-2 border-l-accent-primary"
          : "hover:bg-bg-tertiary active:translate-y-[1px]"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-medium text-text-primary truncate">{job.title}</h3>
          <div className="flex items-center gap-2 mt-0.5">
            {job.company_name && (
              <span className="text-xs text-text-secondary flex items-center gap-1">
                <Buildings size={12} weight="bold" />
                {job.company_name}
              </span>
            )}
            {job.location && (
              <span className="text-xs text-text-muted flex items-center gap-1">
                <MapPin size={12} weight="bold" />
                {job.location}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleStar();
          }}
          className="p-2 -m-2 shrink-0 rounded-[var(--radius-md)] hover:bg-bg-tertiary transition-[background-color,transform] duration-[var(--transition-fast)] active:translate-y-[1px]"
          aria-label={job.is_starred ? "Unstar job" : "Star job"}
        >
          <Star
            size={16}
            weight={job.is_starred ? "fill" : "regular"}
            className={cn("transition-colors", "text-accent-warning")}
          />
        </button>
      </div>
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        <MatchScoreBadge score={job.match_score} />
        <FreshnessBadge score={job.freshness_score} />
        {job.remote_type && (
          <Badge variant="info" size="sm">
            <Monitor size={12} weight="bold" className="mr-0.5" />
            {job.remote_type}
          </Badge>
        )}
        <SalaryRange min={job.salary_min} max={job.salary_max} period={job.salary_period} />
        {job.posted_at && (
          <span className="text-xs text-text-muted flex items-center gap-1 ml-auto">
            <Clock size={12} weight="bold" />
            {formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })}
          </span>
        )}
      </div>
    </div>
  );
}
