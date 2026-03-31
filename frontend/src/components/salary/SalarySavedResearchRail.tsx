import { Building } from "@phosphor-icons/react";
import { StateBlock } from "../system/StateBlock";
import { SalarySavedResearchCard, SalaryScopeRail } from "./SalaryWidgets";

export interface SalarySavedResearchRailEntry {
  id: string;
  title: string;
  company: string;
  location: string;
  market: string;
  timestamp: string;
}

export function SalarySavedResearchRail({
  entries,
  onSelect,
}: {
  entries: SalarySavedResearchRailEntry[];
  onSelect: (entryId: string) => void;
}) {
  return (
    <div className="space-y-4">
      {entries.length ? (
        entries.map((entry) => (
          <SalarySavedResearchCard
            key={entry.id}
            title={entry.title}
            company={entry.company}
            location={entry.location}
            market={entry.market}
            timestamp={entry.timestamp}
            onSelect={() => onSelect(entry.id)}
          />
        ))
      ) : (
        <StateBlock
          tone="muted"
          icon={<Building size={18} weight="bold" />}
          title="Recent research"
          description="Saved salary pulls and offer evaluations will collect here."
        />
      )}
      <SalaryScopeRail
        title="Reading the result"
        description="Use P50 as the anchor, P25/P75 as the bracket, and the coaching output as the plan."
      />
    </div>
  );
}
