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
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DailyStats, FunnelData, SkillStats, SourceStats } from "../../api/analytics";
import Card from "../ui/Card";

const COLORS = ["#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#a855f7", "#22c55e"];

const tooltipStyle = {
  contentStyle: {
    backgroundColor: "var(--color-bg-secondary)",
    border: "1px solid var(--color-border)",
    borderRadius: "0.75rem",
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
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={daily || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
                tickFormatter={(d: string) => d.slice(5)}
              />
              <YAxis tick={{ fontSize: 11, fill: "var(--color-text-muted)" }} />
              <Tooltip {...tooltipStyle} />
              <Line
                type="monotone"
                dataKey="jobs_scraped"
                stroke="var(--color-accent-primary)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Application Funnel */}
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Application Funnel
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={funnel || []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                type="number"
                tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
              />
              <YAxis
                type="category"
                dataKey="stage"
                tick={{ fontSize: 11, fill: "var(--color-text-secondary)" }}
                width={100}
              />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {(funnel || []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Jobs by Source */}
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Jobs by Source
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={sources || []}
                dataKey="total_jobs"
                nameKey="source"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({
                  name,
                  percent,
                }: {
                  name?: string;
                  percent?: number;
                }) => `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {(sources || []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend
                wrapperStyle={{ fontSize: "0.75rem", color: "#a0a0b8" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Top Skills */}
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Top Skills Requested
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={skills || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="skill"
                tick={{ fontSize: 10, fill: "var(--color-text-muted)" }}
                interval={0}
                angle={-30}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fontSize: 11, fill: "var(--color-text-muted)" }} />
              <Tooltip {...tooltipStyle} />
              <Bar
                dataKey="count"
                fill="var(--color-accent-primary)"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
