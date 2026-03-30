import { ArrowClockwise, Pause, Play, Plus } from "@phosphor-icons/react";
import Button from "../ui/Button";

type AutoApplyPageHeaderActionsProps = {
  activeTab: string;
  onRefresh: () => void;
  onPause: () => void;
  onRun: () => void;
  onAddProfile: () => void;
  onAddRule: () => void;
  pausePending: boolean;
  runPending: boolean;
  operatorBusy: boolean;
};

export function AutoApplyPageHeaderActions({
  activeTab,
  onRefresh,
  onPause,
  onRun,
  onAddProfile,
  onAddRule,
  pausePending,
  runPending,
  operatorBusy,
}: AutoApplyPageHeaderActionsProps) {
  return (
    <>
      <Button
        variant="secondary"
        onClick={onRefresh}
        icon={<ArrowClockwise size={16} weight="bold" />}
      >
        Refresh
      </Button>
      <Button
        variant="secondary"
        loading={pausePending}
        disabled={operatorBusy}
        onClick={onPause}
        icon={<Pause size={16} weight="bold" />}
      >
        Pause
      </Button>
      <Button
        loading={runPending}
        disabled={operatorBusy}
        onClick={onRun}
        icon={<Play size={16} weight="bold" />}
      >
        Run now
      </Button>
      {activeTab === "profiles" ? (
        <Button
          variant="secondary"
          onClick={onAddProfile}
          icon={<Plus size={16} weight="bold" />}
        >
          Add Profile
        </Button>
      ) : null}
      {activeTab === "rules" ? (
        <Button
          variant="secondary"
          onClick={onAddRule}
          icon={<Plus size={16} weight="bold" />}
        >
          Add Rule
        </Button>
      ) : null}
    </>
  );
}
