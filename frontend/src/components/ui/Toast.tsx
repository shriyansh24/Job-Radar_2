import {
  CheckCircle,
  Info,
  WarningCircle,
  X,
  XCircle,
} from "@phosphor-icons/react";
import { useCallback, useEffect, useState } from "react";
import { cn } from "../../lib/utils";
import { registerToastHandler } from "./toastService";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  useEffect(() => {
    registerToastHandler(addToast);
    return () => {
      registerToastHandler(null);
    };
  }, [addToast]);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const icons = {
    success: <CheckCircle size={18} weight="bold" className="text-accent-success" />,
    error: <XCircle size={18} weight="bold" className="text-accent-danger" />,
    warning: <WarningCircle size={18} weight="bold" className="text-accent-warning" />,
    info: <Info size={18} weight="bold" className="text-accent-primary" />,
  };

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "flex items-center gap-3 px-4 py-3 bg-bg-secondary border border-border rounded-[var(--radius-xl)] shadow-[var(--shadow-lg)] min-w-[300px] max-w-[420px]",
          )}
        >
          {icons[t.type]}
          <span className="flex-1 text-sm text-text-primary">{t.message}</span>
          <button
            onClick={() => removeToast(t.id)}
            className="p-1 rounded-[var(--radius-md)] text-text-muted hover:text-text-primary hover:bg-bg-tertiary transition-[background-color,color,transform] duration-[var(--transition-fast)] active:translate-y-[1px]"
            aria-label="Dismiss notification"
          >
            <X size={14} weight="bold" />
          </button>
        </div>
      ))}
    </div>
  );
}
