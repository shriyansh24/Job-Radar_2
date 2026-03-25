import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { DailyStats, FunnelData, SkillStats, SourceStats } from "../../api/analytics";
import Card from "../ui/Card";

const SERIES_COLORS = [
  "var(--color-chart-series-1)",
  "var(--color-chart-series-2)",
  "var(--color-chart-series-3)",
  "var(--color-chart-series-4)",
  "var(--color-chart-series-5)",
  "var(--color-chart-series-6)",
];

type PieTextAnchor = "start" | "middle" | "end" | "inherit" | undefined;
type PieDominantBaseline =
  | "auto"
  | "middle"
  | "central"
  | "hanging"
  | "alphabetic"
  | "ideographic"
  | "mathematical"
  | "text-after-edge"
  | "text-before-edge"
  | "inherit"
  | "use-script"
  | "no-change"
  | "reset-size"
  | undefined;

const tooltipStyle = {
  contentStyle: {
    backgroundColor: "var(--color-chart-tooltip-bg)",
    border: "2px solid var(--color-chart-tooltip-border)",
    borderRadius: "0px",
    color: "var(--color-text-primary)",
    fontSize: "0.75rem",
    fontFamily: "var(--font-mono)",
    boxShadow: "var(--shadow-sm)",
  },
  labelStyle: {
    color: "var(--color-chart-label)",
    fontSize: "0.6875rem",
    letterSpacing: "0.12em",
    textTransform: "uppercase" as const,
  },
  itemStyle: {
    color: "var(--color-text-primary)",
    fontSize: "0.75rem",
  },
};

interface AnalyticsChartsProps {
  daily: DailyStats[] | undefined;
  funnel: FunnelData[] | undefined;
  sources: SourceStats[] | undefined;
  skills: SkillStats[] | undefined;
}

function ChartViewport({
  children,
  className = "h-64",
}: {
  children: (dimensions: { width: number; height: number }) => ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const update = () => {
      const rect = node.getBoundingClientRect();
      setDimensions({
        width: Math.floor(rect.width),
        height: Math.floor(rect.height),
      });
    };

    update();
    const observer = new ResizeObserver(update);
    observer.observe(node);

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={className}>
      {dimensions.width > 0 && dimensions.height > 0 ? (
        children(dimensions)
      ) : (
        <div className="h-full w-full animate-pulse border-2 border-border bg-[var(--color-bg-tertiary)]" />
      )}
    </div>
  );
}

export default function AnalyticsCharts({
  daily,
  funnel,
  sources,
  skills,
}: AnalyticsChartsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Jobs Over Time */}
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Jobs Scraped (Last 30 Days)
        </h2>
        <ChartViewport>
          {({ width, height }) => (
            <LineChart width={width} height={height} data={daily || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-chart-grid)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--color-chart-axis)" }}
                tickFormatter={(d: string) => d.slice(5)}
              />
              <YAxis tick={{ fontSize: 11, fill: "var(--color-chart-axis)" }} />
              <Tooltip {...tooltipStyle} />
              <Line
                type="monotone"
                dataKey="jobs_scraped"
                stroke="var(--color-chart-series-1)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          )}
        </ChartViewport>
      </Card>

      {/* Application Funnel */}
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Application Funnel
        </h2>
        <ChartViewport>
          {({ width, height }) => (
            <BarChart width={width} height={height} data={funnel || []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-chart-grid)" />
              <XAxis
                type="number"
                tick={{ fontSize: 11, fill: "var(--color-chart-axis)" }}
              />
              <YAxis
                type="category"
                dataKey="stage"
                tick={{ fontSize: 11, fill: "var(--color-chart-label)" }}
                width={100}
              />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" radius={[0, 0, 0, 0]}>
                {(funnel || []).map((_, i) => (
                  <Cell key={i} fill={SERIES_COLORS[i % SERIES_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ChartViewport>
      </Card>

      {/* Jobs by Source */}
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Jobs by Source
        </h2>
        <ChartViewport>
          {({ width, height }) => (
            <PieChart width={width} height={height}>
              <Pie
                data={sources || []}
                dataKey="total_jobs"
                nameKey="source"
                cx="50%"
                cy="50%"
                outerRadius={Math.max(60, Math.min(width, height) * 0.28)}
                label={({
                  name,
                  percent,
                  x,
                  y,
                  textAnchor,
                  dominantBaseline,
                }: {
                  name?: string;
                  percent?: number;
                  x?: number;
                  y?: number;
                  textAnchor?: PieTextAnchor;
                  dominantBaseline?: PieDominantBaseline;
                }) => (
                  <text
                    x={x}
                    y={y}
                    fill="var(--color-chart-label)"
                    fontSize="11"
                    fontFamily="var(--font-mono)"
                    textAnchor={textAnchor}
                    dominantBaseline={dominantBaseline}
                  >
                    {`${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  </text>
                )}
                labelLine={false}
              >
                {(sources || []).map((_, i) => (
                  <Cell key={i} fill={SERIES_COLORS[i % SERIES_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend
                wrapperStyle={{
                  fontSize: "0.75rem",
                  color: "var(--color-chart-label)",
                  fontFamily: "var(--font-mono)",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                }}
              />
            </PieChart>
          )}
        </ChartViewport>
      </Card>

      {/* Top Skills */}
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Top Skills Requested
        </h2>
        <ChartViewport>
          {({ width, height }) => (
            <BarChart width={width} height={height} data={skills || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-chart-grid)" />
              <XAxis
                dataKey="skill"
                tick={{ fontSize: 10, fill: "var(--color-chart-axis)" }}
                interval={0}
                angle={-30}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fontSize: 11, fill: "var(--color-chart-axis)" }} />
              <Tooltip {...tooltipStyle} />
              <Bar
                dataKey="count"
                fill="var(--color-chart-series-1)"
                radius={[0, 0, 0, 0]}
              />
            </BarChart>
          )}
        </ChartViewport>
      </Card>
    </div>
  );
}
