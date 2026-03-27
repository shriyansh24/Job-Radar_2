import { BookOpen, Sparkle, X } from "@phosphor-icons/react";
import Button from "../ui/Button";
import Textarea from "../ui/Textarea";
import { SettingsSection } from "../system/SettingsSection";
import { StateBlock } from "../system/StateBlock";
import { BRUTAL_BUTTON, BRUTAL_FIELD, BRUTAL_PANEL } from "./constants";

type ProfileAnswerBankSectionProps = {
  answerBank: Record<string, string>;
  onGenerate: () => void;
  onUpdateAnswer: (question: string, answer: string) => void;
  onRemoveAnswer: (question: string) => void;
  isGenerating: boolean;
};

function ProfileAnswerBankSection({ answerBank, onGenerate, onUpdateAnswer, onRemoveAnswer, isGenerating }: ProfileAnswerBankSectionProps) {
  return (
    <SettingsSection
      title="Answer bank"
      description="Reusable interview answers generated from the current profile."
      className={BRUTAL_PANEL}
      actions={
        <Button type="button" variant="secondary" className={BRUTAL_BUTTON} onClick={onGenerate} loading={isGenerating} icon={<Sparkle size={16} weight="bold" />}>
          Generate
        </Button>
      }
    >
      <div className="space-y-4">
        {Object.keys(answerBank).length ? (
          Object.entries(answerBank).map(([question, answer]) => (
            <div key={question} className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <label className="text-sm font-medium text-foreground">{question}</label>
                <button type="button" onClick={() => onRemoveAnswer(question)} className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] px-2 py-1 text-[var(--color-text-muted)] hover:text-[var(--color-accent-danger)]">
                  <X size={14} weight="bold" />
                </button>
              </div>
              <Textarea value={answer} onChange={(event) => onUpdateAnswer(question, event.target.value)} className={`${BRUTAL_FIELD} min-h-[100px]`} />
            </div>
          ))
        ) : (
          <StateBlock tone="muted" icon={<BookOpen size={18} weight="bold" />} title="No answers yet" description="Generate them from the profile source of truth or add your own manually." />
        )}
      </div>
    </SettingsSection>
  );
}

export { ProfileAnswerBankSection };
export type { ProfileAnswerBankSectionProps };
