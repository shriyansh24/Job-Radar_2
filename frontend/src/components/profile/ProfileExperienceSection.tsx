import { Plus } from "@phosphor-icons/react";
import Input from "../ui/Input";
import Textarea from "../ui/Textarea";
import Button from "../ui/Button";
import { SettingsSection } from "../system/SettingsSection";
import type { FormState } from "./constants";
import { BRUTAL_BUTTON, BRUTAL_FIELD, EMPTY_EXPERIENCE } from "./constants";
import { EntryCard } from "./ProfileControls";

type ProfileExperienceSectionProps = {
  form: FormState;
  onUpdateField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
};

function ProfileExperienceSection({ form, onUpdateField }: ProfileExperienceSectionProps) {
  return (
    <SettingsSection title="Experience" description="Role history shown in prepare and intelligence surfaces." className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]">
      <div className="space-y-3">
        {form.experience.map((entry, index) => (
          <EntryCard
            key={`${entry.company}-${index}`}
            title={entry.company || `Role ${index + 1}`}
            onRemove={() => onUpdateField("experience", form.experience.filter((_, itemIndex) => itemIndex !== index))}
          >
            <div className="grid gap-3 md:grid-cols-2">
              <Input value={entry.company} onChange={(event) => { const next = [...form.experience]; next[index] = { ...entry, company: event.target.value }; onUpdateField("experience", next); }} placeholder="Company" className={BRUTAL_FIELD} />
              <Input value={entry.title} onChange={(event) => { const next = [...form.experience]; next[index] = { ...entry, title: event.target.value }; onUpdateField("experience", next); }} placeholder="Title" className={BRUTAL_FIELD} />
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <Input value={entry.start_date ?? ""} onChange={(event) => { const next = [...form.experience]; next[index] = { ...entry, start_date: event.target.value || null }; onUpdateField("experience", next); }} placeholder="Start date" className={BRUTAL_FIELD} />
              <Input value={entry.end_date ?? ""} onChange={(event) => { const next = [...form.experience]; next[index] = { ...entry, end_date: event.target.value || null }; onUpdateField("experience", next); }} placeholder="End date or Present" className={BRUTAL_FIELD} />
            </div>
            <Textarea
              className={`${BRUTAL_FIELD} mt-3 min-h-[110px]`}
              value={entry.description ?? ""}
              onChange={(event) => { const next = [...form.experience]; next[index] = { ...entry, description: event.target.value || null }; onUpdateField("experience", next); }}
              placeholder="What you owned, shipped, or learned."
            />
          </EntryCard>
        ))}
        <Button type="button" variant="secondary" className={BRUTAL_BUTTON} onClick={() => onUpdateField("experience", [...form.experience, { ...EMPTY_EXPERIENCE }])} icon={<Plus size={14} weight="bold" />}>
          Add experience
        </Button>
      </div>
    </SettingsSection>
  );
}

export { ProfileExperienceSection };
export type { ProfileExperienceSectionProps };
