import { SettingsSection } from "../system/SettingsSection";
import type { ThemeFamily, ThemeMode } from "../../store/useUIStore";
import { THEME_FAMILY_OPTIONS, THEME_MODE_OPTIONS } from "./constants";

type SettingsAppearanceSectionProps = {
  mode: ThemeMode;
  themeFamily: ThemeFamily;
  onModeChange: (mode: ThemeMode) => void;
  onThemeFamilyChange: (family: ThemeFamily) => void;
};

function SettingsAppearanceSection({
  mode,
  themeFamily,
  onModeChange,
  onThemeFamilyChange,
}: SettingsAppearanceSectionProps) {
  return (
    <SettingsSection title="Appearance" description="Choose mode and theme family." className="border-2 border-border bg-card shadow-hard-xl">
      <div className="space-y-8">
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">Mode</h4>
            <p className="mt-1 text-sm text-muted-foreground">Switch between light and dark.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {THEME_MODE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onModeChange(option.value)}
                className={`border-2 px-4 py-4 font-mono text-[11px] font-bold uppercase tracking-[0.18em] ${
                  mode === option.value ? "border-border bg-primary text-primary-foreground shadow-none" : "border-border bg-background text-foreground"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-foreground">Theme family</h4>
            <p className="mt-1 text-sm text-muted-foreground">Pick the active visual system.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {THEME_FAMILY_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onThemeFamilyChange(option.value)}
                className={`flex items-center justify-between gap-3 border-2 px-4 py-4 text-left ${
                  themeFamily === option.value ? "border-border bg-primary text-primary-foreground shadow-none" : "border-border bg-background text-foreground"
                }`}
              >
                <span className="font-mono text-[11px] font-bold uppercase tracking-[0.18em]">{option.label}</span>
                <span className={`size-3 border-2 border-current ${themeFamily === option.value ? "bg-primary-foreground" : "bg-primary"}`} />
              </button>
            ))}
          </div>
        </div>
      </div>
    </SettingsSection>
  );
}

export { SettingsAppearanceSection };
export type { SettingsAppearanceSectionProps };
