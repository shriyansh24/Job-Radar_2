import { Lightning, Plus, Shield, ShieldCheck } from "@phosphor-icons/react";

import type { AutoApplyRule } from "../../api/auto-apply";
import { SectionHeader } from "../system/SectionHeader";
import { SplitWorkspace } from "../system/SplitWorkspace";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import { SkeletonCard } from "../ui/Skeleton";
import { RuleCard } from "./RuleCard";

type AutoApplyRulesTabPanelProps = {
  rules: AutoApplyRule[] | undefined;
  rulesLoading: boolean;
  pendingCount: number;
  onShowCreateRule: () => void;
  onToggleRule: (rule: AutoApplyRule) => void;
};

export function AutoApplyRulesTabPanel({
  rules,
  rulesLoading,
  pendingCount,
  onShowCreateRule,
  onToggleRule,
}: AutoApplyRulesTabPanelProps) {
  return (
    <SplitWorkspace
      primary={
        <Surface padding="lg" radius="xl">
          <SectionHeader
            title="Rules"
            description="Rules gate which jobs can auto-submit."
            action={
              <Button
                variant="secondary"
                onClick={onShowCreateRule}
                icon={<Plus size={14} weight="bold" />}
              >
                Add Rule
              </Button>
            }
          />
          <div className="mt-5">
            {rulesLoading ? (
              <div className="grid gap-4 md:grid-cols-2">
                {Array.from({ length: 2 }).map((_, index) => (
                  <SkeletonCard key={index} />
                ))}
              </div>
            ) : !rules?.length ? (
              <EmptyState
                icon={<Shield size={40} weight="bold" />}
                title="No rules yet"
                description="Create rules to gate automation."
                action={{ label: "Add Rule", onClick: onShowCreateRule }}
              />
            ) : (
              <div className="grid gap-4">
                {rules.map((rule) => (
                  <RuleCard
                    key={rule.id}
                    rule={rule}
                    onToggleActive={() => onToggleRule(rule)}
                  />
                ))}
              </div>
            )}
          </div>
        </Surface>
      }
      secondary={
        <div className="space-y-4">
          <StateBlock
            tone="neutral"
            icon={<ShieldCheck size={18} weight="bold" />}
            title="Rule logic"
            description="Required keywords shrink the pool. Excluded keywords block bad fits."
          />
          <StateBlock
            tone={pendingCount ? "warning" : "danger"}
            icon={<Lightning size={18} weight="bold" />}
            title="Run posture"
            description={
              pendingCount
                ? `${pendingCount} pending item${pendingCount === 1 ? "" : "s"} still in queue.`
                : "If success drops, narrow active rules before adding profiles."
            }
          />
        </div>
      }
    />
  );
}
