import { ArrowUp, Building, Lightbulb, Minus } from "@phosphor-icons/react";
import { type OfferEvaluation, type SalaryResearch } from "../../api/salary";
import { Surface } from "../system/Surface";
import Badge from "../ui/Badge";

function formatSalary(value: number | null | undefined): string {
  if (!value) return "-";
  if (value >= 1000) {
    return `$${Math.round(value / 1000)}k`;
  }
  return `$${value.toLocaleString()}`;
}

export function SalaryRangeBar({ research }: { research: SalaryResearch }) {
  const markers = [
    { label: "P25", value: research.p25 ?? 0, accent: "text-text-primary" },
    { label: "P50", value: research.p50 ?? 0, accent: "text-accent-primary" },
    { label: "P75", value: research.p75 ?? 0, accent: "text-text-primary" },
    { label: "P90", value: research.p90 ?? 0, accent: "text-text-primary" },
  ];
  const values = markers.map((marker) => marker.value).filter((value) => value > 0);
  if (values.length < 2) return null;

  const floor = Math.min(...values);
  const ceiling = Math.max(...values);
  const range = ceiling - floor;
  if (range <= 0) return null;

  const getPosition = (value: number) => ((value - floor) / range) * 100;

  return (
    <div className="space-y-5">
      <div className="hero-panel relative h-12 px-4">
        <div className="absolute left-4 right-4 top-1/2 h-2 -translate-y-1/2 bg-border" />
        <div
          className="absolute top-1/2 h-4 -translate-y-1/2 border-2 border-border bg-accent-primary/20"
          style={{
            left: `calc(${getPosition(research.p25 ?? floor)}% + 0.5rem)`,
            width: `${getPosition(research.p75 ?? ceiling) - getPosition(research.p25 ?? floor)}%`,
          }}
        />
        {markers.map((marker) => (
          <div
            key={marker.label}
            className="absolute top-1/2 size-4 -translate-y-1/2 border-2 border-border"
            style={{
              left: `calc(${getPosition(marker.value)}% + 0.5rem)`,
              backgroundColor: marker.label === "P50" ? "var(--color-accent-primary)" : "var(--card)",
            }}
          />
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2 text-center sm:grid-cols-4">
        {markers.map((item) => (
          <div key={item.label} className="border-2 border-border bg-card px-2 py-3">
            <p className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              {item.label}
            </p>
            <p className={`mt-2 text-lg font-black uppercase tracking-[-0.05em] ${item.accent}`}>
              {formatSalary(item.value)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SalaryVerdictDisplay({ evaluation }: { evaluation: OfferEvaluation }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Badge variant="info" size="md">
          <Lightbulb size={14} weight="bold" />
          <span className="ml-1">Negotiation guidance</span>
        </Badge>
        {evaluation.counter_offer ? (
          <Badge variant="success" size="md">
            <ArrowUp size={14} weight="bold" />
            <span className="ml-1">Counter {formatSalary(evaluation.counter_offer)}</span>
          </Badge>
        ) : null}
        {evaluation.walkaway_point ? (
          <Badge variant="warning" size="md">
            <Minus size={14} weight="bold" />
            <span className="ml-1">Walkaway {formatSalary(evaluation.walkaway_point)}</span>
          </Badge>
        ) : null}
      </div>

      <div className="brutal-panel px-4 py-4 text-sm leading-6 text-text-secondary">
        {evaluation.assessment}
      </div>

      {evaluation.talking_points.length ? (
        <div className="space-y-3">
          <h4 className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Talking points
          </h4>
          <div className="space-y-2">
            {evaluation.talking_points.map((tip, index) => (
              <div key={`${tip}-${index}`} className="brutal-panel px-4 py-3 text-sm leading-6 text-text-secondary">
                {tip}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {evaluation.negotiation_script ? (
        <div className="space-y-3">
          <h4 className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Script
          </h4>
          <div className="border-2 border-border bg-card px-4 py-4 text-sm leading-6 text-text-secondary">
            {evaluation.negotiation_script}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function SalarySavedResearchCard({
  title,
  company,
  location,
  market,
  timestamp,
  onSelect,
}: {
  title: string;
  company: string;
  location: string;
  market: string;
  timestamp: string;
  onSelect: () => void;
}) {
  return (
    <Surface tone="default" padding="md" radius="xl" interactive className="brutal-panel">
      <button type="button" className="block w-full text-left" onClick={onSelect}>
        <div className="space-y-3">
          <div>
            <div className="text-lg font-black uppercase tracking-[-0.04em] text-text-primary">{title}</div>
            <p className="mt-1 text-sm leading-6 text-text-secondary">
              {[company || null, location || null].filter(Boolean).join(" / ") || "General market"}
            </p>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-2xl font-black uppercase tracking-[-0.05em] text-accent-primary">{market}</span>
            <span className="text-sm text-muted-foreground">{timestamp}</span>
          </div>
        </div>
      </button>
    </Surface>
  );
}

export function SalaryScopeRail({ title, description }: { title: string; description: string }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
        <Building size={16} weight="bold" className="text-[var(--color-accent-primary)]" />
        {title}
      </div>
      <div className="brutal-panel p-4 text-sm leading-6 text-text-secondary">{description}</div>
    </div>
  );
}
