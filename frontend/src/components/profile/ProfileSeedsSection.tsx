import { SettingsSection } from "../system/SettingsSection";
import type { FormState } from "./constants";
import { TagEditor } from "./ProfileControls";

type ProfileSeedsSectionProps = {
  form: FormState;
  onUpdateField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
};

function ProfileSeedsSection({ form, onUpdateField }: ProfileSeedsSectionProps) {
  return (
    <SettingsSection title="Search seeds" description="The initial phrases and target companies that inform discovery." className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]">
      <div className="space-y-5">
        <TagEditor label="Search queries" placeholder="e.g. Senior frontend engineer" items={form.search_queries} onAdd={(value) => onUpdateField("search_queries", [...form.search_queries, value])} onRemove={(index) => onUpdateField("search_queries", form.search_queries.filter((_, i) => i !== index))} />
        <TagEditor label="Search locations" placeholder="e.g. Remote, New York" items={form.search_locations} onAdd={(value) => onUpdateField("search_locations", [...form.search_locations, value])} onRemove={(index) => onUpdateField("search_locations", form.search_locations.filter((_, i) => i !== index))} />
        <TagEditor label="Watchlist companies" placeholder="e.g. Stripe" items={form.watchlist_companies} onAdd={(value) => onUpdateField("watchlist_companies", [...form.watchlist_companies, value])} onRemove={(index) => onUpdateField("watchlist_companies", form.watchlist_companies.filter((_, i) => i !== index))} />
      </div>
    </SettingsSection>
  );
}

export { ProfileSeedsSection };
export type { ProfileSeedsSectionProps };
