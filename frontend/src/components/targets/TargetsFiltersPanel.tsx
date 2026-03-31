import Select from "../ui/Select";
import { Surface } from "../system/Surface";

export interface TargetsFilters {
  priority_class: string;
  ats_vendor: string;
  status: string;
}

export function TargetsFiltersPanel({
  filters,
  onPriorityChange,
  onVendorChange,
  onStatusChange,
}: {
  filters: TargetsFilters;
  onPriorityChange: (value: string) => void;
  onVendorChange: (value: string) => void;
  onStatusChange: (value: string) => void;
}) {
  return (
    <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-1">
        <Select
          value={filters.priority_class}
          onChange={(event) => onPriorityChange(event.target.value)}
          options={[
            { value: "watchlist", label: "Watchlist" },
            { value: "hot", label: "Hot" },
            { value: "warm", label: "Warm" },
            { value: "cool", label: "Cool" },
          ]}
          placeholder="All priorities"
          label="Priority"
        />
        <Select
          value={filters.ats_vendor}
          onChange={(event) => onVendorChange(event.target.value)}
          options={[
            { value: "greenhouse", label: "Greenhouse" },
            { value: "lever", label: "Lever" },
            { value: "ashby", label: "Ashby" },
            { value: "workday", label: "Workday" },
            { value: "unknown", label: "Unknown" },
          ]}
          placeholder="All vendors"
          label="ATS vendor"
        />
        <Select
          value={filters.status}
          onChange={(event) => onStatusChange(event.target.value)}
          options={[
            { value: "enabled", label: "Enabled" },
            { value: "disabled", label: "Disabled" },
            { value: "quarantined", label: "Quarantined" },
          ]}
          placeholder="All statuses"
          label="Status"
        />
      </div>
    </Surface>
  );
}
