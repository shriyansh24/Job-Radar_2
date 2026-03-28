import { CheckCircle } from "@phosphor-icons/react";
import Button from "../ui/Button";

type SettingsPageHeaderProps = {
  onSave: () => void;
  isSaving: boolean;
};

function SettingsPageHeader({ onSave, isSaving }: SettingsPageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="command-label mb-1">Operations</p>
        <h1 className="font-headline text-3xl font-black uppercase tracking-tight">Settings</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Account, theme, integrations, and saved searches.
        </p>
      </div>
      <Button
        variant="primary"
        onClick={onSave}
        loading={isSaving}
        icon={<CheckCircle size={16} weight="bold" />}
      >
        Save changes
      </Button>
    </div>
  );
}

export { SettingsPageHeader };
export type { SettingsPageHeaderProps };
