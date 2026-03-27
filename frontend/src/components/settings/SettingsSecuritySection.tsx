import { Key } from "@phosphor-icons/react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { SettingsSection } from "../system/SettingsSection";

type SettingsSecuritySectionProps = {
  userEmail?: string | null;
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
  onCurrentPasswordChange: (value: string) => void;
  onNewPasswordChange: (value: string) => void;
  onConfirmPasswordChange: (value: string) => void;
  onSubmit: () => void;
  isPending: boolean;
};

function SettingsSecuritySection({
  userEmail,
  currentPassword,
  newPassword,
  confirmPassword,
  onCurrentPasswordChange,
  onNewPasswordChange,
  onConfirmPasswordChange,
  onSubmit,
  isPending,
}: SettingsSecuritySectionProps) {
  return (
    <SettingsSection title="Security" description="Change the current account password." className="border-2 border-border bg-card shadow-hard-xl">
      <div className="p-6">
        <form
          className="max-w-xl space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit();
          }}
        >
          <input
            type="email"
            name="account-email"
            autoComplete="username"
            value={userEmail ?? ""}
            readOnly
            tabIndex={-1}
            aria-hidden="true"
            className="sr-only"
          />
          <Input
            label="Current password"
            type="password"
            autoComplete="current-password"
            name="current-password"
            value={currentPassword}
            onChange={(event) => onCurrentPasswordChange(event.target.value)}
          />
          <Input
            label="New password"
            type="password"
            autoComplete="new-password"
            name="new-password"
            value={newPassword}
            onChange={(event) => onNewPasswordChange(event.target.value)}
          />
          <Input
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            name="confirm-password"
            value={confirmPassword}
            onChange={(event) => onConfirmPasswordChange(event.target.value)}
          />
          <Button type="submit" variant="secondary" loading={isPending} icon={<Key size={16} weight="bold" />}>
            Update password
          </Button>
        </form>
      </div>
    </SettingsSection>
  );
}

export { SettingsSecuritySection };
export type { SettingsSecuritySectionProps };
