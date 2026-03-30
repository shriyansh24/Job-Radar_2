import { Shield, ShieldCheck } from "@phosphor-icons/react";
import type { AutoApplyRule } from "../../api/auto-apply";
import { cn } from "../../lib/utils";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { Surface } from "../system/Surface";
import { CHIP } from "./autoApplyUtils";

export function RuleCard({
  rule,
  onToggleActive,
}: {
  rule: AutoApplyRule;
  onToggleActive: () => void;
}) {
  return (
    <Surface tone="subtle" padding="md" className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold tracking-[-0.04em] text-text-primary">{rule.name}</h3>
            <Badge variant={rule.is_active ? "success" : "default"}>
              {rule.is_active ? "Active" : "Inactive"}
            </Badge>
            {rule.min_match_score !== null ? (
              <span className={cn(CHIP, "bg-background text-text-primary")}>Match {rule.min_match_score}%</span>
            ) : null}
          </div>
          <div className="space-y-2">
            {rule.required_keywords.length ? (
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Required
                </span>
                {rule.required_keywords.map((keyword) => (
                  <Badge key={keyword} variant="success" size="sm">
                    {keyword}
                  </Badge>
                ))}
              </div>
            ) : null}
            {rule.excluded_keywords.length ? (
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Excluded
                </span>
                {rule.excluded_keywords.map((keyword) => (
                  <Badge key={keyword} variant="danger" size="sm">
                    {keyword}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={onToggleActive}
          icon={rule.is_active ? <ShieldCheck size={14} weight="bold" /> : <Shield size={14} weight="bold" />}
        >
          {rule.is_active ? "Deactivate" : "Activate"}
        </Button>
      </div>
    </Surface>
  );
}
