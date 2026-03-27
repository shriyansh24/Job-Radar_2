import { TagRow } from "./TagRow";
import { SectionHeader } from "../system/SectionHeader";

export function OnboardingSearchStep({
  searchQueries,
  searchLocations,
  watchlistCompanies,
  onAdd,
  onRemove,
}: {
  searchQueries: string[];
  searchLocations: string[];
  watchlistCompanies: string[];
  onAdd: (key: "searchQueries" | "searchLocations" | "watchlistCompanies", value: string) => void;
  onRemove: (key: "searchQueries" | "searchLocations" | "watchlistCompanies", index: number) => void;
}) {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Search seeds"
        description="Use compact handles instead of long descriptions. The feed expands from there."
      />
      <div className="space-y-5">
        <TagRow
          label="Job titles"
          placeholder="Software Engineer"
          items={searchQueries}
          onAdd={(value) => onAdd("searchQueries", value)}
          onRemove={(index) => onRemove("searchQueries", index)}
        />
        <TagRow
          label="Locations"
          placeholder="Remote"
          items={searchLocations}
          onAdd={(value) => onAdd("searchLocations", value)}
          onRemove={(index) => onRemove("searchLocations", index)}
        />
        <TagRow
          label="Watchlist companies"
          placeholder="Stripe"
          items={watchlistCompanies}
          onAdd={(value) => onAdd("watchlistCompanies", value)}
          onRemove={(index) => onRemove("watchlistCompanies", index)}
        />
      </div>
    </div>
  );
}
