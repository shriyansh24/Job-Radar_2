import * as React from "react";

import { cn } from "@/lib/utils";

type WorkspaceShellProps = React.HTMLAttributes<HTMLDivElement> & {
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  rail?: React.ReactNode;
  bottomNav?: React.ReactNode;
  contentClassName?: string;
  sidebarCollapsed?: boolean;
};

function WorkspaceShell({
  className,
  sidebar,
  header,
  rail,
  bottomNav,
  children,
  contentClassName,
  sidebarCollapsed = false,
  ...props
}: WorkspaceShellProps) {
  return (
    <div
      className={cn("min-h-[100dvh] bg-background text-foreground", className)}
      {...props}
    >
      {header ? (
        <header className="fixed inset-x-0 top-0 z-50 border-b-2 border-border bg-background shadow-[var(--shadow-sm)]">
          {header}
        </header>
      ) : null}

      {sidebar}

      {rail ? (
        <aside className="fixed right-0 top-[var(--header-height)] hidden h-[calc(100dvh-var(--header-height))] w-[var(--rail-width)] border-l-2 border-border bg-background 2xl:block">
          {rail}
        </aside>
      ) : null}

      <div
        className={cn(
          "min-h-[100dvh] pt-[var(--header-height)] transition-[padding] duration-[var(--transition-normal)]",
          sidebar &&
            (sidebarCollapsed
              ? "xl:pl-[var(--sidebar-width-collapsed)]"
              : "xl:pl-[var(--sidebar-width)]"),
          rail && "2xl:pr-[var(--rail-width)]"
        )}
      >
        <main
          className={cn(
            "min-h-[calc(100dvh-var(--header-height))]",
            contentClassName
          )}
        >
          {children}
        </main>
      </div>

      {bottomNav}
    </div>
  );
}

export { WorkspaceShell };
export type { WorkspaceShellProps };
