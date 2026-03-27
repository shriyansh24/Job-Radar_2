import { Buildings, GraduationCap, MagnifyingGlass } from "@phosphor-icons/react";
import { StateBlock } from "../system/StateBlock";
import { BRUTAL_PANEL } from "./constants";

type ProfileSidebarProps = {
  watchlistCount: number;
  searchSeedCount: number;
};

function ProfileSidebar({ watchlistCount, searchSeedCount }: ProfileSidebarProps) {
  return (
    <div className="space-y-4">
      <StateBlock
        tone="neutral"
        icon={<MagnifyingGlass size={18} weight="bold" />}
        title="Profile usage"
        description="Discovery, onboarding, interview prep, and Copilot all read from this record."
        className={BRUTAL_PANEL}
      />
      <StateBlock
        tone="success"
        icon={<Buildings size={18} weight="bold" />}
        title="Workspace summary"
        description={`${watchlistCount} watchlist companies and ${searchSeedCount} search seeds currently configured.`}
        className={BRUTAL_PANEL}
      />
      <StateBlock
        tone="warning"
        icon={<GraduationCap size={18} weight="bold" />}
        title="Readiness check"
        description="Add at least one role and one search seed to make the other surfaces immediately useful."
        className={BRUTAL_PANEL}
      />
    </div>
  );
}

export { ProfileSidebar };
export type { ProfileSidebarProps };
