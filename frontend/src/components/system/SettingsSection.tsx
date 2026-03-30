import * as React from "react";

import { Surface } from "./Surface";

type SettingsSectionProps = React.HTMLAttributes<HTMLDivElement> & {
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
};

function SettingsSection({
  className,
  title,
  description,
  actions,
  children,
  ...props
}: SettingsSectionProps) {
  return (
    <Surface tone="default" padding="lg" radius="xl" className={className} {...props}>
      <div className="flex flex-col gap-3 border-b-2 border-border pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">{title}</h2>
          {description ? (
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        {actions ? <div className="shrink-0">{actions}</div> : null}
      </div>
      <div className="pt-5">{children}</div>
    </Surface>
  );
}

export { SettingsSection };
export type { SettingsSectionProps };
