import { SpinnerGap } from "@phosphor-icons/react";

export default function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-3">
        <SpinnerGap size={32} weight="bold" className="text-accent-primary animate-spin" />
        <p className="text-sm text-text-muted">Loading...</p>
      </div>
    </div>
  );
}
