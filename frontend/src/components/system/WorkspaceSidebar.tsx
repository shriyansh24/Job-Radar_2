import type { IconProps } from "@phosphor-icons/react"
import { DotsThreeOutlineVertical } from "@phosphor-icons/react"
import { motion } from "framer-motion"
import * as React from "react"

import { cn } from "@/lib/utils"

type WorkspaceNavItem = {
  key: string
  label: string
  href?: string
  icon?: React.ComponentType<IconProps>
  badge?: React.ReactNode
  active?: boolean
  onSelect?: () => void
}

type WorkspaceNavSection = {
  key: string
  label: string
  items: WorkspaceNavItem[]
}

type WorkspaceSidebarProps = React.HTMLAttributes<HTMLDivElement> & {
  brand?: React.ReactNode
  sections: WorkspaceNavSection[]
  collapsed?: boolean
  footer?: React.ReactNode
}

function WorkspaceSidebar({
  className,
  brand,
  sections,
  collapsed = false,
  footer,
  ...props
}: WorkspaceSidebarProps) {
  return (
    <div
      className={cn(
        "flex h-full min-h-[100dvh] flex-col bg-sidebar text-sidebar-foreground",
        className
      )}
      {...props}
    >
      <div className="border-b border-sidebar-border px-4 py-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            {brand ?? (
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-[var(--radius-lg)] bg-sidebar-primary text-sidebar-primary-foreground shadow-[var(--shadow-sm)]">
                  JR
                </div>
                {!collapsed ? (
                  <div className="min-w-0">
                    <p className="text-sm font-semibold tracking-[-0.02em]">
                      JobRadar
                    </p>
                    <p className="text-xs text-sidebar-foreground/60">
                      Career OS
                    </p>
                  </div>
                ) : null}
              </div>
            )}
          </div>

          {!collapsed ? (
            <button
              type="button"
              className="inline-flex size-8 items-center justify-center rounded-[var(--radius-md)] text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              aria-label="Sidebar options"
            >
              <DotsThreeOutlineVertical size={18} weight="bold" />
            </button>
          ) : null}
        </div>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
        {sections.map((section, sectionIndex) => (
          <motion.div
            key={section.key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: sectionIndex * 0.04 }}
            className="space-y-2"
          >
            {!collapsed ? (
              <p className="px-2 text-[11px] font-medium uppercase tracking-[0.16em] text-sidebar-foreground/45">
                {section.label}
              </p>
            ) : null}

            <div className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon
                const content = (
                  <>
                    <span
                      className={cn(
                        "flex size-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-transparent transition-colors",
                        item.active
                          ? "bg-sidebar-primary/14 text-sidebar-primary"
                          : "text-sidebar-foreground/62"
                      )}
                    >
                      {Icon ? <Icon size={18} weight="duotone" /> : null}
                    </span>
                    {!collapsed ? (
                      <>
                        <span className="min-w-0 flex-1 truncate text-sm font-medium">
                          {item.label}
                        </span>
                        {item.badge ? (
                          <span className="rounded-full bg-sidebar-accent px-2 py-0.5 text-[11px] font-medium text-sidebar-accent-foreground/75">
                            {item.badge}
                          </span>
                        ) : null}
                      </>
                    ) : (
                      <span className="sr-only">{item.label}</span>
                    )}
                  </>
                )

                const itemClassName = cn(
                  "group flex w-full items-center gap-3 rounded-[var(--radius-lg)] px-2 py-1.5 text-left transition-colors",
                  item.active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "hover:bg-sidebar-accent/70 hover:text-sidebar-accent-foreground"
                )

                if (item.href) {
                  return (
                    <a
                      key={item.key}
                      href={item.href}
                      className={itemClassName}
                      aria-current={item.active ? "page" : undefined}
                    >
                      {content}
                    </a>
                  )
                }

                return (
                  <button
                    key={item.key}
                    type="button"
                    className={itemClassName}
                    onClick={item.onSelect}
                    aria-pressed={item.active || undefined}
                  >
                    {content}
                  </button>
                )
              })}
            </div>
          </motion.div>
        ))}
      </nav>

      {footer ? (
        <div className="border-t border-sidebar-border px-3 py-3">{footer}</div>
      ) : null}
    </div>
  )
}

export { WorkspaceSidebar }
export type { WorkspaceNavItem, WorkspaceNavSection, WorkspaceSidebarProps }
