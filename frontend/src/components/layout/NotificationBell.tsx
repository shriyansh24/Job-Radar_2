import { Bell, Check, Trash } from "@phosphor-icons/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { notificationsApi, type Notification } from "../../api/notifications";
import { cn } from "../../lib/utils";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: countData } = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: notificationsApi.unreadCount,
    refetchInterval: 60_000, // 1 minute — notification count doesn't need to be real-time
  });

  const { data: listData } = useQuery({
    queryKey: ["notifications", "list"],
    queryFn: () => notificationsApi.list(false, 20),
    enabled: open,
  });

  const markRead = useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAllRead = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const deleteNotif = useMutation({
    mutationFn: notificationsApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const unreadCount = countData?.unread_count ?? 0;
  const items = listData?.items ?? [];

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="hard-press relative inline-flex size-10 items-center justify-center border-2 border-border bg-background text-text-secondary shadow-[var(--shadow-xs)] hover:text-text-primary"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
      >
        <Bell size={18} weight={unreadCount > 0 ? "fill" : "bold"} />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex min-h-4 min-w-4 items-center justify-center border-2 border-border bg-accent-primary px-1 font-mono text-[10px] font-bold text-primary-foreground">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-12 z-50 max-h-96 w-[min(22rem,calc(100vw-1.5rem))] overflow-auto border-2 border-border bg-card shadow-[var(--shadow-lg)]"
          >
            <div className="flex items-center justify-between border-b-2 border-border px-4 py-3">
              <span className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-text-primary">
                Notifications
              </span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllRead.mutate()}
                  className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-accent-primary hover:text-accent-primary-hover"
                >
                  Mark all read
                </button>
              )}
            </div>

            {items.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-text-muted">
                No notifications
              </div>
            ) : (
              <ul className="divide-y-2 divide-border/20">
                {items.map((n: Notification) => (
                  <li
                    key={n.id}
                    className={cn(
                      "cursor-pointer px-4 py-3 transition-colors hover:bg-[var(--color-bg-hover)]",
                      !n.read && "bg-[var(--color-accent-primary-subtle)]"
                    )}
                    onClick={() => {
                      if (!n.read) markRead.mutate(n.id);
                      if (n.link) {
                        navigate(n.link);
                        setOpen(false);
                      }
                    }}
                  >
                    <div className="flex min-w-0 items-start gap-3">
                      <div className="mt-0.5 h-3 w-3 border-2 border-border bg-transparent">
                        {!n.read ? <div className="pulse-dot h-full w-full bg-accent-primary" /> : null}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p
                          className={cn(
                            "truncate text-sm uppercase tracking-[-0.03em]",
                            n.read ? "text-text-secondary" : "font-semibold text-text-primary"
                          )}
                        >
                          {n.title}
                        </p>
                        {n.body && (
                          <p className="mt-1 line-clamp-2 text-xs leading-5 text-text-muted">
                            {n.body}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="mt-3 flex gap-1">
                      {!n.read && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            markRead.mutate(n.id);
                          }}
                          className="hard-press border-2 border-border bg-background p-1 text-text-muted shadow-[var(--shadow-xs)]"
                          title="Mark as read"
                        >
                          <Check size={14} />
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteNotif.mutate(n.id);
                        }}
                        className="hard-press border-2 border-border bg-background p-1 text-text-muted shadow-[var(--shadow-xs)]"
                        title="Delete"
                      >
                        <Trash size={14} />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
