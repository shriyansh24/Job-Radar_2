import { cn } from '../../lib/utils';

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export default function Tabs({ tabs, activeTab, onChange, className }: TabsProps) {
  return (
    <div
      className={cn(
        "overflow-x-auto border-b-2 border-border pb-4",
        className
      )}
    >
      <div className="flex min-w-max gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={cn(
              "inline-flex min-h-11 items-center gap-2 border-2 px-4 py-2 text-[11px] font-mono font-bold uppercase tracking-[0.18em] transition-[background-color,color,transform,box-shadow] duration-[var(--transition-fast)]",
              activeTab === tab.id
                ? "border-border bg-primary text-primary-foreground shadow-[var(--shadow-xs)]"
                : "border-border bg-background text-text-secondary shadow-[var(--shadow-xs)] hover:bg-[var(--color-bg-secondary)] hover:text-foreground"
            )}
          >
            {tab.icon}
            <span className="whitespace-nowrap">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
