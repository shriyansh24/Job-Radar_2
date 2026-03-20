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
        className="relative p-2 rounded-[var(--radius-md)] hover:bg-bg-tertiary text-text-secondary transition-[background-color,color] duration-[var(--transition-fast)]"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
      >
        <Bell size={18} weight={unreadCount > 0 ? "fill" : "bold"} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent-primary px-1 text-[10px] font-bold text-white">
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
            className="absolute right-0 top-12 z-50 w-80 max-h-96 overflow-auto rounded-[var(--radius-lg)] border border-border bg-bg-secondary shadow-xl"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <span className="text-sm font-medium text-text-primary">
                Notifications
              </span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllRead.mutate()}
                  className="text-xs text-accent-primary hover:underline"
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
              <ul className="divide-y divide-border">
                {items.map((n: Notification) => (
                  <li
                    key={n.id}
                    className={cn(
                      "flex items-start gap-3 px-4 py-3 hover:bg-bg-tertiary/50 transition-colors cursor-pointer",
                      !n.read && "bg-accent-primary/5"
                    )}
                    onClick={() => {
                      if (!n.read) markRead.mutate(n.id);
                      if (n.link) {
                        navigate(n.link);
                        setOpen(false);
                      }
                    }}
                  >
                    <div className="flex-1 min-w-0">
                      <p
                        className={cn(
                          "text-sm truncate",
                          n.read ? "text-text-secondary" : "text-text-primary font-medium"
                        )}
                      >
                        {n.title}
                      </p>
                      {n.body && (
                        <p className="text-xs text-text-muted mt-0.5 line-clamp-2">
                          {n.body}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-1 shrink-0">
                      {!n.read && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            markRead.mutate(n.id);
                          }}
                          className="p-1 rounded hover:bg-bg-tertiary text-text-muted"
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
                        className="p-1 rounded hover:bg-bg-tertiary text-text-muted"
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
