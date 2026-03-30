import { MagnifyingGlass, RocketLaunch, UserCircle } from "@phosphor-icons/react";
import { StateBlock } from "../system/StateBlock";

const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";

export function OnboardingHeroPanel({
  step,
  stepLabels,
  title,
  description,
  callout,
  profileName,
  searchCount,
}: {
  step: number;
  stepLabels: readonly string[];
  title: string;
  description: string;
  callout: string;
  profileName: string;
  searchCount: number;
}) {
  return (
    <section className="overflow-hidden border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-[var(--shadow-lg)]">
      <div className="grid gap-0 lg:grid-cols-[minmax(0,1.5fr)_minmax(260px,0.85fr)]">
        <div className="p-5 sm:p-6 lg:p-8">
          <div className="flex flex-wrap items-center gap-2">
            <span className={CHIP}>Step {step + 1}</span>
            <span className={CHIP}>{stepLabels[step]}</span>
          </div>
          <div className="mt-5 flex items-start gap-4">
            <div className="flex size-14 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)]">
              <RocketLaunch size={28} weight="bold" />
            </div>
            <div className="space-y-3">
              <h2 className="font-display text-[clamp(2rem,4vw,3.6rem)] font-black uppercase tracking-[-0.07em] text-text-primary">
                {title}
              </h2>
              <p className="max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">{description}</p>
            </div>
          </div>
        </div>

        <div className="border-t-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] p-5 sm:p-6 lg:border-l-2 lg:border-t-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">Step signal</div>
          <div className="mt-3 h-4 border-2 border-[var(--color-text-primary)] bg-background">
            <div
              className="h-full bg-accent-primary transition-[width] duration-[var(--transition-normal)]"
              style={{ width: `${((step + 1) / stepLabels.length) * 100}%` }}
            />
          </div>
          <p className="mt-4 text-sm leading-6 text-text-secondary">{callout}</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
            <StateBlock
              tone="muted"
              icon={<UserCircle size={18} weight="bold" />}
              title="Identity"
              description={profileName || "No name captured yet."}
            />
            <StateBlock
              tone="warning"
              icon={<MagnifyingGlass size={18} weight="bold" />}
              title="Discovery"
              description={searchCount ? `${searchCount} title seeds queued.` : "Add titles and companies next."}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
