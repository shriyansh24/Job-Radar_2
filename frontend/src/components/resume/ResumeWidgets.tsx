import { Clock, FileText, Star } from "@phosphor-icons/react";
import { format } from "date-fns";
import { type ResumeTailorResponse, type ResumeVersion } from "../../api/resume";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import Badge from "../ui/Badge";

export function ResumeVersionCard({
  version,
  onPreview,
}: {
  version: ResumeVersion;
  onPreview: () => void;
}) {
  return (
    <Surface
      tone="default"
      padding="lg"
      radius="xl"
      interactive
      onClick={onPreview}
      className="space-y-4"
    >
      <div className="flex items-start gap-3">
        <div className="flex size-12 shrink-0 items-center justify-center border-2 border-border bg-[var(--color-bg-tertiary)]">
          <FileText size={22} weight="bold" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="truncate text-sm font-semibold text-text-primary">
              {version.filename ?? "Untitled resume"}
            </p>
            {version.is_default ? <Badge variant="success">Default</Badge> : null}
          </div>
          <p className="mt-2 flex items-center gap-1 text-xs text-text-muted">
            <Clock size={12} weight="bold" />
            {format(new Date(version.created_at), "PP")}
          </p>
        </div>
      </div>

      <div className="border-t-2 border-border pt-4">
        <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Parsed preview
        </div>
        <p className="mt-2 line-clamp-4 text-sm leading-6 text-text-secondary">
          {version.parsed_text || "No parsed text yet."}
        </p>
      </div>
    </Surface>
  );
}

export function ResumeTailorResultPanel({ result }: { result: ResumeTailorResponse }) {
  return (
    <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
      <SectionHeader
        title="Tailored resume"
        description="Score delta, rewritten content, and missing requirements from the tailoring pipeline."
      />

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="brutal-panel p-5">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Summary
          </div>
          <p className="mt-3 text-sm leading-6 text-text-secondary">
            {result.summary || "No summary returned."}
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="brutal-panel p-4">
            <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              ATS before
            </div>
            <div className="mt-3 text-3xl font-black uppercase tracking-[-0.05em] text-text-primary">
              {result.ats_score_before}
            </div>
          </div>
          <div className="brutal-panel p-4">
            <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              ATS after
            </div>
            <div className="mt-3 text-3xl font-black uppercase tracking-[-0.05em] text-accent-primary">
              {result.ats_score_after}
            </div>
          </div>
        </div>
      </div>

      {result.enhanced_bullets.length ? (
        <div className="mt-5 space-y-2">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Enhanced bullets
          </div>
          <div className="space-y-2">
            {result.enhanced_bullets.map((bullet, index) => (
              <div key={`${bullet.original}-${index}`} className="brutal-panel px-4 py-3 text-sm text-text-secondary">
                <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Original
                </div>
                <div className="mt-2">{bullet.original}</div>
                <div className="mt-4 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Revised
                </div>
                <div className="mt-2 text-text-primary">{bullet.enhanced}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {result.reordered_experience.length ? (
        <div className="mt-5 space-y-2">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Reordered experience
          </div>
          <div className="grid gap-3 lg:grid-cols-2">
            {result.reordered_experience.map((entry) => (
              <div key={entry.company} className="brutal-panel p-4">
                <div className="text-sm font-semibold uppercase tracking-[-0.03em] text-text-primary">
                  {entry.company}
                </div>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-text-secondary">
                  {entry.bullets.map((bullet, index) => (
                    <li key={`${entry.company}-${index}`}>{bullet}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {result.skills_section.length ? (
        <div className="mt-5 space-y-2">
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Skills section
          </div>
          <div className="flex flex-wrap gap-2">
            {result.skills_section.map((skill) => (
              <Badge key={skill} variant="info">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}
    </Surface>
  );
}

export function ResumeStatusRail({
  versionCount,
  selectedResume,
}: {
  versionCount: number;
  selectedResume: string;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
        <Star size={16} weight="bold" className="text-[var(--color-accent-success)]" />
        Workspace state
      </div>
      <div className="brutal-panel p-4">
        <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Versions
        </div>
        <div className="mt-2 text-lg font-black uppercase tracking-[-0.04em] text-text-primary">
          {versionCount}
        </div>
      </div>
      <div className="brutal-panel p-4">
        <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Selection
        </div>
        <div className="mt-2 text-sm text-text-secondary">{selectedResume ? "Ready" : "None selected"}</div>
      </div>
    </div>
  );
}

export function ResumeCouncilSummary({
  score,
  evaluations,
}: {
  score: number;
  evaluations: Array<{ model: string; score: number; feedback: string }>;
}) {
  return (
    <div className="mt-6 space-y-4">
      <div className="hero-panel p-5 text-center">
        <div className="mono-num text-5xl font-bold text-text-primary">{score.toFixed(1)}</div>
        <p className="mt-2 text-sm text-muted-foreground">Average score</p>
      </div>
      {evaluations.map((evaluation) => (
        <Surface key={evaluation.model} tone="subtle" padding="md" radius="xl">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-semibold text-text-primary">{evaluation.model}</span>
            <Badge
              variant={evaluation.score >= 8 ? "success" : evaluation.score >= 5 ? "warning" : "danger"}
            >
              {evaluation.score}/10
            </Badge>
          </div>
          <p className="mt-3 text-sm leading-6 text-text-secondary">{evaluation.feedback}</p>
        </Surface>
      ))}
    </div>
  );
}
