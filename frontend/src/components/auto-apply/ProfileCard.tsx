import { Envelope, User } from "@phosphor-icons/react";
import type { AutoApplyProfile } from "../../api/auto-apply";
import { cn } from "../../lib/utils";
import Badge from "../ui/Badge";
import { Surface } from "../system/Surface";
import { CHIP } from "./autoApplyUtils";

export function ProfileCard({ profile }: { profile: AutoApplyProfile }) {
  return (
    <Surface tone="subtle" padding="md" className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold tracking-[-0.04em] text-text-primary">{profile.name}</h3>
            {profile.is_active ? <Badge variant="success">Active</Badge> : null}
          </div>
          <p className="mt-2 flex items-center gap-2 text-sm text-text-secondary">
            <Envelope size={14} weight="bold" />
            {profile.email}
          </p>
        </div>
        <div className="flex size-11 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-background">
          <User size={18} weight="bold" />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {profile.phone ? <span className={cn(CHIP, "bg-background text-text-primary")}>Phone</span> : null}
        {profile.linkedin_url ? (
          <span className={cn(CHIP, "bg-accent-primary/10 text-text-primary")}>LinkedIn</span>
        ) : null}
        {profile.github_url ? (
          <span className={cn(CHIP, "bg-accent-primary/10 text-text-primary")}>GitHub</span>
        ) : null}
        {profile.portfolio_url ? (
          <span className={cn(CHIP, "bg-accent-primary/10 text-text-primary")}>Portfolio</span>
        ) : null}
        {profile.cover_letter_template ? (
          <span className={cn(CHIP, "bg-accent-warning/10 text-text-primary")}>Template</span>
        ) : null}
      </div>
    </Surface>
  );
}
