import { FloppyDisk, Sparkle } from "@phosphor-icons/react";
import Button from "../ui/Button";
import { PageHeader } from "../system/PageHeader";
import { BRUTAL_BUTTON, BRUTAL_PANEL, BRUTAL_PRIMARY_BUTTON } from "./constants";

type ProfileActionsProps = {
  onGenerateAnswers: () => void;
  onSaveProfile: () => void;
  isGenerating: boolean;
  isSaving: boolean;
};

function ProfileActions({ onGenerateAnswers, onSaveProfile, isGenerating, isSaving }: ProfileActionsProps) {
  return (
    <PageHeader
      eyebrow="Prepare"
      title="Profile"
      description="Keep the source-of-truth profile here."
      className={BRUTAL_PANEL}
      actions={
        <>
          <Button variant="secondary" className={BRUTAL_BUTTON} onClick={onGenerateAnswers} loading={isGenerating} icon={<Sparkle size={16} weight="bold" />}>
            Generate answers
          </Button>
          <Button className={BRUTAL_PRIMARY_BUTTON} onClick={onSaveProfile} loading={isSaving} icon={<FloppyDisk size={16} weight="bold" />}>
            Save profile
          </Button>
        </>
      }
    />
  );
}

export { ProfileActions };
export type { ProfileActionsProps };
