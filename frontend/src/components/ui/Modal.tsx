import { X } from "@phosphor-icons/react";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useId, useRef } from "react";
import { cn } from "../../lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export default function Modal({ open, onClose, title, children, size = 'md', className }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          ref={overlayRef}
          className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(9,9,11,0.72)] p-4 backdrop-blur-[2px]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={(e) => {
            if (e.target === overlayRef.current) onClose();
          }}
        >
          <motion.div
            className={cn(
              "flex max-h-[85vh] w-full flex-col rounded-none border-2 border-border bg-card shadow-[var(--shadow-lg)]",
              sizes[size],
              className
            )}
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? titleId : undefined}
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 260, damping: 22 }}
          >
            {title && (
              <div className="flex items-center justify-between border-b-2 border-border px-5 py-4">
                <div className="space-y-1">
                  <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    Overlay
                  </div>
                  <h2 id={titleId} className="font-display text-xl font-black uppercase tracking-[-0.05em] text-text-primary">
                    {title}
                  </h2>
                </div>
                <button
                  onClick={onClose}
                  className="hard-press border-2 border-border bg-background p-2 text-text-muted shadow-[var(--shadow-xs)] hover:text-text-primary"
                  aria-label="Close modal"
                >
                  <X size={18} weight="bold" />
                </button>
              </div>
            )}
            <div className="flex-1 overflow-auto p-5 sm:p-6">{children}</div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
