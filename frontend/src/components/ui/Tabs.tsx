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
        "overflow-x-auto border-2 border-border bg-[var(--color-bg-secondary)] p-1 shadow-[var(--shadow-sm)]",
        className
      )}
    >
      <div className="flex min-w-max gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={cn(
              "inline-flex min-h-10 items-center gap-2 border-2 px-4 py-2 text-[10px] font-mono font-bold uppercase tracking-[0.18em] transition-[background-color,color,transform,box-shadow,border-color] duration-[var(--transition-fast)]",
              activeTab === tab.id
                ? "border-border bg-card text-foreground shadow-[var(--shadow-sm)]"
                : "border-transparent bg-transparent text-text-secondary shadow-none hover:border-border hover:bg-card hover:text-foreground"
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
