import type React from "react";

type SettingsTab = "profile" | "appearance" | "workspace" | "security" | "integrations" | "searches" | "data";

type TabIcon = React.ComponentType<{ size?: number; weight?: "bold" }>;

type TabItem = {
  id: SettingsTab;
  label: string;
  icon: TabIcon;
};

type SettingsTabNavProps = {
  tabs: TabItem[];
  activeTab: SettingsTab;
  onSelect: (tab: SettingsTab) => void;
  className?: string;
};

function SettingsTabNav({ tabs, activeTab, onSelect, className }: SettingsTabNavProps) {
  return (
    <div className={className}>
      <div className="space-y-1">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onSelect(item.id)}
            className={`flex w-full items-center gap-3 border-2 px-4 py-3 text-left font-mono text-[11px] font-bold uppercase tracking-[0.18em] transition-colors ${
              activeTab === item.id
                ? "border-border bg-primary text-primary-foreground"
                : "border-transparent bg-transparent text-foreground hover:border-border hover:bg-background"
            }`}
          >
            <item.icon size={16} weight="bold" />
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export type { SettingsTab, TabItem };
export { SettingsTabNav };
