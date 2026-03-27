import { CurrencyDollar } from "@phosphor-icons/react";
import Input from "../ui/Input";
import { SettingsSection } from "../system/SettingsSection";
import type { FormState } from "./constants";
import { BRUTAL_FIELD, JOB_TYPE_OPTIONS, REMOTE_TYPE_OPTIONS } from "./constants";
import { ToggleGroup } from "./ProfileControls";

type ProfilePreferencesSectionProps = {
  form: FormState;
  onUpdateField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
};

function ProfilePreferencesSection({ form, onUpdateField }: ProfilePreferencesSectionProps) {
  return (
    <SettingsSection title="Preferences" description="Job type, remote preference, and compensation bounds." className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]">
      <div className="space-y-5">
        <ToggleGroup label="Preferred job types" options={JOB_TYPE_OPTIONS} selected={form.preferred_job_types} onChange={(values) => onUpdateField("preferred_job_types", values)} />
        <ToggleGroup label="Preferred remote types" options={REMOTE_TYPE_OPTIONS} selected={form.preferred_remote_types} onChange={(values) => onUpdateField("preferred_remote_types", values)} />
        <div className="grid gap-4 md:grid-cols-2">
          <Input label="Salary minimum" type="number" value={form.salary_min} onChange={(event) => onUpdateField("salary_min", event.target.value)} icon={<CurrencyDollar size={16} weight="bold" />} className={BRUTAL_FIELD} />
          <Input label="Salary maximum" type="number" value={form.salary_max} onChange={(event) => onUpdateField("salary_max", event.target.value)} icon={<CurrencyDollar size={16} weight="bold" />} className={BRUTAL_FIELD} />
        </div>
      </div>
    </SettingsSection>
  );
}

export { ProfilePreferencesSection };
export type { ProfilePreferencesSectionProps };
