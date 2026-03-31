import { Scroll } from "@phosphor-icons/react";
import type { CoverLetterResult } from "../../api/copilot";
import EmptyState from "../ui/EmptyState";
import { SkeletonCard } from "../ui/Skeleton";
import { Surface } from "../system/Surface";
import { SplitWorkspace } from "../system/SplitWorkspace";
import { StateBlock } from "../system/StateBlock";
import { VaultCoverLetterCard } from "./VaultPanels";

export function VaultCoverLettersTab({
  coverLetters,
  lettersLoading,
  onEdit,
  onDelete,
}: {
  coverLetters: CoverLetterResult[] | undefined;
  lettersLoading: boolean;
  onEdit: (letter: CoverLetterResult) => void;
  onDelete: (letterId: string) => void;
}) {
  return (
    <SplitWorkspace
      primary={
        lettersLoading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <SkeletonCard key={index} />
            ))}
          </div>
        ) : !coverLetters || coverLetters.length === 0 ? (
          <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
            <EmptyState
              icon={<Scroll size={40} weight="bold" />}
              title="No cover letters"
              description="Generate a letter in Copilot and it will appear here."
            />
          </Surface>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {coverLetters.map((letter) => (
              <VaultCoverLetterCard
                key={letter.id}
                letter={letter}
                onEdit={() => onEdit(letter)}
                onDelete={() => onDelete(letter.id)}
              />
            ))}
          </div>
        )
      }
      secondary={
        <div className="space-y-4">
          <StateBlock
            tone="warning"
            icon={<Scroll size={18} weight="bold" />}
            title="Draft behavior"
            description="Letter drafts stay editable here before reuse."
          />
        </div>
      }
    />
  );
}
