import { ArrowClockwise, CheckCircle, PencilSimple, Trash } from "@phosphor-icons/react";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Skeleton from "../ui/Skeleton";
import { SettingsSection } from "../system/SettingsSection";
import type { SavedSearch } from "../../api/settings";

type SettingsSearchesSectionProps = {
  searches?: SavedSearch[] | null;
  loading: boolean;
  checkingSearchId?: string | null;
  onCreate: () => void;
  onEdit: (search?: SavedSearch) => void;
  onToggle: (search: SavedSearch) => void;
  onCheck: (search: SavedSearch) => void;
  onDelete: (search: SavedSearch) => void;
};

function SettingsSearchesSection({
  searches,
  loading,
  checkingSearchId,
  onCreate,
  onEdit,
  onToggle,
  onCheck,
  onDelete,
}: SettingsSearchesSectionProps) {
  return (
    <SettingsSection
      title="Saved searches"
      description="Reusable filters and alert settings."
      actions={
        <Button variant="primary" onClick={onCreate} icon={<PencilSimple size={16} weight="bold" />}>
          New search
        </Button>
      }
      className="border-2 border-border bg-card shadow-hard-xl"
    >
      <div className="space-y-4">
        {loading ? (
          Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} variant="rect" className="h-24 w-full" />)
        ) : searches && searches.length > 0 ? (
          searches.map((search) => (
            <div key={search.id} className="border-2 border-border p-4">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">{search.name}</h4>
                    <Badge variant={search.alert_enabled ? "success" : "default"} size="sm" className="rounded-none">
                      {search.alert_enabled ? "Alerts on" : "Alerts off"}
                    </Badge>
                  </div>
                  <p className="max-w-3xl text-sm text-muted-foreground">{JSON.stringify(search.filters ?? {}, null, 2)}</p>
                  <div className="space-y-1 text-xs text-muted-foreground">
                    <p>
                      Last checked{" "}
                      {search.last_checked_at
                        ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(search.last_checked_at))
                        : "Never checked"}
                    </p>
                    <p>
                      Last match{" "}
                      {search.last_matched_at
                        ? `${search.last_match_count} job${search.last_match_count === 1 ? "" : "s"} at ${new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(search.last_matched_at))}`
                        : "No alert sent yet"}
                    </p>
                    {search.last_error ? (
                      <p className="text-accent-danger">Last error: {search.last_error}</p>
                    ) : null}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => onCheck(search)}
                    loading={checkingSearchId === search.id}
                    disabled={!search.alert_enabled}
                    icon={<ArrowClockwise size={16} weight="bold" />}
                  >
                    Check now
                  </Button>
                  <Button variant="secondary" onClick={() => onToggle(search)} icon={<CheckCircle size={16} weight="bold" />}>
                    Toggle
                  </Button>
                  <Button variant="secondary" onClick={() => onEdit(search)} icon={<PencilSimple size={16} weight="bold" />}>
                    Edit
                  </Button>
                  <Button variant="danger" onClick={() => onDelete(search)} icon={<Trash size={16} weight="bold" />}>
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="border-2 border-dashed border-border p-8 text-center">
            <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">No saved searches</h4>
            <p className="mt-2 text-sm text-muted-foreground">Create a search to save filters and alerts.</p>
            <Button variant="primary" className="mt-4" onClick={onCreate} icon={<PencilSimple size={16} weight="bold" />}>
              Create search
            </Button>
          </div>
        )}
      </div>
    </SettingsSection>
  );
}

export { SettingsSearchesSection };
export type { SettingsSearchesSectionProps };
