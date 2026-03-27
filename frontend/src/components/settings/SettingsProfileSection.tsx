import Input from "../ui/Input";
import { SettingsSection } from "../system/SettingsSection";

type SettingsProfileSectionProps = {
  userEmail?: string | null;
  displayName?: string | null;
};

function SettingsProfileSection({ userEmail, displayName }: SettingsProfileSectionProps) {
  return (
    <SettingsSection title="Profile" description="Current signed-in account." className="border-2 border-border bg-card shadow-hard-xl">
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <div className="flex size-16 shrink-0 items-center justify-center border-2 border-border bg-secondary text-xl font-black uppercase">
            {(displayName || userEmail || "U")[0].toUpperCase()}
          </div>
          <div>
            <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-muted">Signed in as</p>
            <p className="mt-1 text-base font-semibold text-foreground">{displayName || userEmail || "Unknown user"}</p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Email" type="email" value={userEmail ?? ""} readOnly />
          <Input label="Display name" value={displayName ?? ""} readOnly />
        </div>
      </div>
    </SettingsSection>
  );
}

export { SettingsProfileSection };
export type { SettingsProfileSectionProps };
