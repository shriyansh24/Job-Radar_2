import Toggle from "../ui/Toggle";
import { SettingsSection } from "../system/SettingsSection";

type SettingsWorkspaceSectionProps = {
  notificationsEnabled: boolean;
  autoApplyEnabled: boolean;
  onNotificationsChange: (value: boolean) => void;
  onAutoApplyChange: (value: boolean) => void;
};

function SettingsWorkspaceSection({
  notificationsEnabled,
  autoApplyEnabled,
  onNotificationsChange,
  onAutoApplyChange,
}: SettingsWorkspaceSectionProps) {
  return (
    <SettingsSection title="Workspace" description="Global workspace switches." className="border-2 border-border bg-card shadow-hard-xl">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-4 border-2 border-border p-4">
          <div>
            <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">Notifications</h4>
            <p className="mt-1 text-sm text-muted-foreground">Enable system alerts.</p>
          </div>
          <Toggle checked={notificationsEnabled} onChange={onNotificationsChange} />
        </div>

        <div className="flex items-center justify-between gap-4 border-2 border-border p-4">
          <div>
            <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">Auto apply</h4>
            <p className="mt-1 text-sm text-muted-foreground">Allow automated submissions.</p>
          </div>
          <Toggle checked={autoApplyEnabled} onChange={onAutoApplyChange} />
        </div>
      </div>
    </SettingsSection>
  );
}

export { SettingsWorkspaceSection };
export type { SettingsWorkspaceSectionProps };
