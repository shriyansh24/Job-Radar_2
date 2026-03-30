import Input from "../ui/Input";
import Button from "../ui/Button";
import { SettingsSection } from "../system/SettingsSection";
import type { FormState } from "./constants";
import { BRUTAL_BUTTON, BRUTAL_FIELD, EMPTY_EDUCATION } from "./constants";
import { EntryCard } from "./ProfileControls";
import { Plus } from "@phosphor-icons/react";

type ProfileEducationSectionProps = {
  form: FormState;
  onUpdateField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
};

function ProfileEducationSection({ form, onUpdateField }: ProfileEducationSectionProps) {
  return (
    <SettingsSection title="Education" description="A compact history of academic context used for matching and interview prep." className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]">
      <div className="space-y-3">
        {form.education.map((entry, index) => (
          <EntryCard
            key={`${entry.school}-${index}`}
            title={entry.school || `Education ${index + 1}`}
            onRemove={() => onUpdateField("education", form.education.filter((_, itemIndex) => itemIndex !== index))}
          >
            <div className="grid gap-3 md:grid-cols-3">
              <Input value={entry.school} onChange={(event) => { const next = [...form.education]; next[index] = { ...entry, school: event.target.value }; onUpdateField("education", next); }} placeholder="School" className={BRUTAL_FIELD} />
              <Input value={entry.degree} onChange={(event) => { const next = [...form.education]; next[index] = { ...entry, degree: event.target.value }; onUpdateField("education", next); }} placeholder="Degree" className={BRUTAL_FIELD} />
              <Input value={entry.field} onChange={(event) => { const next = [...form.education]; next[index] = { ...entry, field: event.target.value }; onUpdateField("education", next); }} placeholder="Field" className={BRUTAL_FIELD} />
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <Input value={entry.start_date ?? ""} onChange={(event) => { const next = [...form.education]; next[index] = { ...entry, start_date: event.target.value || null }; onUpdateField("education", next); }} placeholder="Start date" className={BRUTAL_FIELD} />
              <Input value={entry.end_date ?? ""} onChange={(event) => { const next = [...form.education]; next[index] = { ...entry, end_date: event.target.value || null }; onUpdateField("education", next); }} placeholder="End date" className={BRUTAL_FIELD} />
            </div>
          </EntryCard>
        ))}
        <Button type="button" variant="secondary" className={BRUTAL_BUTTON} onClick={() => onUpdateField("education", [...form.education, { ...EMPTY_EDUCATION }])} icon={<Plus size={14} weight="bold" />}>
          Add education
        </Button>
      </div>
    </SettingsSection>
  );
}

export { ProfileEducationSection };
export type { ProfileEducationSectionProps };
