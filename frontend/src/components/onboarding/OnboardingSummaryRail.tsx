import { RocketLaunch, Sparkle } from "@phosphor-icons/react";
import { SectionHeader } from "../system/SectionHeader";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";

export function OnboardingSummaryRail({
  summaryItems,
  stepLabel,
  callout,
}: {
  summaryItems: Array<{ key: string; label: string; value: string | number; hint: string }>;
  stepLabel: string;
  callout: string;
}) {
  return (
    <div className="space-y-4">
      {summaryItems.map((item) => (
        <StateBlock
          key={item.key}
          tone="neutral"
          title={item.label}
          description={`${item.value} - ${item.hint}`}
        />
      ))}
      <Surface padding="lg" radius="xl">
        <SectionHeader
          title="Current move"
          description={`You are on ${stepLabel}. Finish with what you know now and tune later from Settings.`}
        />
        <div className="mt-4 space-y-3">
          <StateBlock tone="warning" icon={<Sparkle size={18} weight="bold" />} title="Guidance" description={callout} />
          <StateBlock
            tone="success"
            icon={<RocketLaunch size={18} weight="bold" />}
            title="Outcome"
            description="A completed setup unlocks discovery, saved filters, and better prep surfaces."
          />
        </div>
      </Surface>
    </div>
  );
}
