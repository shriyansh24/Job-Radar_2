import { Briefcase } from "@phosphor-icons/react";
import { lazy, Suspense } from "react";
import type {
  AnalyticsPatternsResponse,
  DailyStats,
  FunnelData,
  SkillStats,
  SourceStats,
} from "../../api/analytics";
import EmptyState from "../ui/EmptyState";
import Skeleton from "../ui/Skeleton";
import { AnalyticsPatternsPanel } from "./AnalyticsPatternsPanel";
import { Surface } from "../system/Surface";
import { SectionHeader } from "../system/SectionHeader";
import Badge from "../ui/Badge";

const Charts = lazy(() => import("./AnalyticsCharts"));

function ChartsSkeleton() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="border-2 border-border bg-card p-4 shadow-[var(--shadow-sm)]">
          <Skeleton variant="text" className="mb-4 h-4 w-1/3" />
          <Skeleton variant="rect" className="h-64 w-full" />
        </div>
      ))}
    </div>
  );
}

type AnalyticsPrimaryColumnProps = {
  daily: DailyStats[] | undefined;
  funnel: FunnelData[] | undefined;
  sources: SourceStats[] | undefined;
  skills: SkillStats[] | undefined;
  patterns: AnalyticsPatternsResponse | undefined;
  patternsLoading: boolean;
};

function AnalyticsPrimaryColumn({
  daily,
  funnel,
  sources,
  skills,
  patterns,
  patternsLoading,
}: AnalyticsPrimaryColumnProps) {
  return (
    <div className="space-y-4">
      <Surface tone="default" padding="lg" radius="xl">
        <SectionHeader
          title="Trend"
          description="History, response rate, and source mix stay on one surface for quick comparison."
          action={<Badge variant="info">Lazy loaded</Badge>}
        />
        <div className="mt-5">
          <Suspense fallback={<ChartsSkeleton />}>
            <Charts daily={daily} funnel={funnel} sources={sources} skills={skills} />
          </Suspense>
        </div>
      </Surface>

      <AnalyticsPatternsPanel patterns={patterns} loading={patternsLoading} />

      <Surface tone="subtle" padding="lg" radius="xl">
        <SectionHeader
          title="Skills pulse"
          description="The most frequent skill signals coming back from recent jobs."
          action={<Badge variant={skills?.length ? "success" : "default"}>{skills?.length ?? 0}</Badge>}
        />
        <div className="mt-4 flex flex-wrap gap-2">
          {skills?.length ? (
            skills.slice(0, 8).map((skill) => (
              <span
                key={skill.skill}
                className="brutal-chip bg-[var(--color-bg-secondary)] text-text-primary"
              >
                {skill.skill}
              </span>
            ))
          ) : (
            <EmptyState
              icon={<Briefcase size={32} weight="bold" />}
              title="No skill data yet"
              description="Once scrapers and saved searches have data, the skill pulse will appear here."
            />
          )}
        </div>
      </Surface>
    </div>
  );
}

export { AnalyticsPrimaryColumn };
