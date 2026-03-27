import { Surface } from "../system/Surface";

type ProfileHeroProps = {
  userEmail?: string | null;
};

function ProfileHero({ userEmail }: ProfileHeroProps) {
  return (
    <Surface tone="default" padding="none" radius="xl" className="overflow-hidden">
      <div className="grid gap-5 border-b-2 border-[var(--color-text-primary)] px-5 py-5 lg:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.8fr)] lg:px-6 lg:py-6">
        <div className="space-y-3">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[var(--color-accent-primary)]">Prepare / Profile</div>
          <h1 className="font-display text-[clamp(2.6rem,6vw,4.5rem)] font-black uppercase tracking-[-0.08em]">Profile ledger</h1>
          <p className="max-w-3xl text-sm leading-7 text-[var(--color-text-secondary)] sm:text-base">
            Keep the source-of-truth profile here. This surface stores identity, preferences, and background data.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
          <div className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)] p-4">
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Signed in</div>
            <div className="mt-3 font-mono text-lg font-bold">{userEmail ?? "Unknown"}</div>
          </div>
          <div className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)] p-4">
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Source of truth</div>
            <div className="mt-3 font-mono text-lg font-bold text-[var(--color-accent-primary)]">Profile ledger</div>
          </div>
        </div>
      </div>
    </Surface>
  );
}

export { ProfileHero };
export type { ProfileHeroProps };
