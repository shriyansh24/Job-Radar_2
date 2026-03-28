import { Envelope, Plus, Pulse, User } from "@phosphor-icons/react";

import type { AutoApplyProfile, AutoApplyRun } from "../../api/auto-apply";
import { SectionHeader } from "../system/SectionHeader";
import { SplitWorkspace } from "../system/SplitWorkspace";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import { SkeletonCard } from "../ui/Skeleton";
import { ProfileCard } from "./ProfileCard";

type AutoApplyProfilesTabPanelProps = {
  profiles: AutoApplyProfile[] | undefined;
  profilesLoading: boolean;
  latestRun: AutoApplyRun | null;
  onShowCreateProfile: () => void;
};

export function AutoApplyProfilesTabPanel({
  profiles,
  profilesLoading,
  latestRun,
  onShowCreateProfile,
}: AutoApplyProfilesTabPanelProps) {
  return (
    <SplitWorkspace
      primary={
        <Surface padding="lg" radius="xl">
          <SectionHeader
            title="Profiles"
            description="Profiles carry contact fields and templates."
            action={
              <Button
                variant="secondary"
                onClick={onShowCreateProfile}
                icon={<Plus size={14} weight="bold" />}
              >
                Add Profile
              </Button>
            }
          />
          <div className="mt-5">
            {profilesLoading ? (
              <div className="grid gap-4 md:grid-cols-2">
                {Array.from({ length: 2 }).map((_, index) => (
                  <SkeletonCard key={index} />
                ))}
              </div>
            ) : !profiles?.length ? (
              <EmptyState
                icon={<User size={40} weight="bold" />}
                title="No profiles yet"
                description="Create the first profile."
                action={{ label: "Add Profile", onClick: onShowCreateProfile }}
              />
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                {profiles.map((profile) => (
                  <ProfileCard key={profile.id} profile={profile} />
                ))}
              </div>
            )}
          </div>
        </Surface>
      }
      secondary={
        <div className="space-y-4">
          <StateBlock
            tone="success"
            icon={<Pulse size={18} weight="bold" />}
            title="Active profile"
            description={
              profiles?.find((profile) => profile.is_active)
                ? "Primary profile is active."
                : "No active profile is marked yet."
            }
          />
          <StateBlock
            tone={latestRun?.status === "failed" ? "danger" : "warning"}
            icon={<Envelope size={18} weight="bold" />}
            title="Latest operator signal"
            description={
              latestRun
                ? `${latestRun.status} - ${Object.keys(latestRun.fields_filled ?? {}).length} fields filled`
                : "Run the first batch to see field coverage."
            }
          />
        </div>
      }
    />
  );
}
