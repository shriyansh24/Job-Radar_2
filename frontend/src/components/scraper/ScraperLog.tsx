import { CaretDown, DotsSixVertical, Pause, Play, X } from "@phosphor-icons/react";
import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";
import { scraperApi, type ScraperEvent } from "../../api/scraper";

interface LogEntry {
  id: number;
  type: string;
  data: string;
  timestamp: string;
}

export default function ScraperLog() {
  const [open, setOpen] = useState(false);
  const [paused, setPaused] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const idCounter = useRef(0);

  // Draggable toggle button position
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0, posX: 0, posY: 0 });
  const btnRef = useRef<HTMLButtonElement>(null);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      dragging.current = true;
      dragStart.current = { x: e.clientX, y: e.clientY, posX: pos.x, posY: pos.y };
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
    },
    [pos],
  );

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging.current) return;
    const dx = e.clientX - dragStart.current.x;
    const dy = e.clientY - dragStart.current.y;
    setPos({ x: dragStart.current.posX + dx, y: dragStart.current.posY + dy });
  }, []);

  const onPointerUp = useCallback(
    (e: React.PointerEvent) => {
      if (!dragging.current) return;
      dragging.current = false;
      const dx = Math.abs(e.clientX - dragStart.current.x);
      const dy = Math.abs(e.clientY - dragStart.current.y);
      // If moved less than 4px, treat as click
      if (dx < 4 && dy < 4) {
        setOpen((o) => !o);
      }
    },
    [],
  );

  useEffect(() => {
    if (!open) return;

    const eventSource = new EventSource(scraperApi.stream());
    let mounted = true;

    eventSource.onmessage = (event) => {
      if (!mounted || paused) return;
      try {
        const parsed = JSON.parse(event.data) as ScraperEvent;
        setLogs((prev) => [
          ...prev.slice(-200),
          {
            id: ++idCounter.current,
            type: parsed.type,
            data: parsed.data,
            timestamp: parsed.timestamp || new Date().toISOString(),
          },
        ]);
      } catch {
        setLogs((prev) => [
          ...prev.slice(-200),
          {
            id: ++idCounter.current,
            type: "info",
            data: event.data,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    };

    eventSource.onerror = () => {
      if (mounted) {
        setLogs((prev) => [
          ...prev,
          {
            id: ++idCounter.current,
            type: "error",
            data: "SSE connection lost. Reconnecting...",
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    };

    return () => {
      mounted = false;
      eventSource.close();
    };
  }, [open, paused]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (!paused) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, paused]);

  const typeColors: Record<string, string> = {
    scraper_started: "text-[var(--color-accent-info)]",
    job_found: "text-[var(--color-accent-secondary)]",
    scraper_completed: "text-[var(--color-accent-secondary)]",
    scraper_error: "text-[var(--color-accent-danger)]",
    error: "text-[var(--color-accent-danger)]",
    info: "text-text-muted",
  };

  return (
    <>
      {/* Draggable toggle button */}
      <button
        ref={btnRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        style={{
          transform: `translate(${pos.x}px, ${pos.y}px)`,
          touchAction: "none",
        }}
        className="fixed bottom-4 right-4 z-40 flex items-center gap-1.5 rounded-[var(--radius-lg)] border-2 border-border bg-bg-secondary px-3 py-2 text-sm text-text-secondary transition-colors select-none cursor-grab hover:text-text-primary active:cursor-grabbing shadow-none"
      >
        <DotsSixVertical size={12} className="text-text-muted shrink-0" />
        <CaretDown size={14} className={open ? "rotate-180 transition-transform" : "transition-transform"} />
        Scraper Log
        {logs.length > 0 && (
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-accent-primary/20 text-accent-primary">
            {logs.length}
          </span>
        )}
      </button>

      {/* Log drawer */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed bottom-0 right-0 z-50 flex h-64 w-full max-w-lg flex-col rounded-tl-[var(--radius-lg)] border-l-2 border-t-2 border-border bg-bg-secondary shadow-none"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-border">
              <span className="text-xs font-medium text-text-primary">Live Scraper Log</span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPaused(!paused)}
                  className="p-1 rounded hover:bg-bg-tertiary text-text-muted"
                  title={paused ? "Resume" : "Pause"}
                >
                  {paused ? <Play size={14} /> : <Pause size={14} />}
                </button>
                <button
                  onClick={() => setLogs([])}
                  className="px-2 py-0.5 rounded text-[10px] text-text-muted hover:bg-bg-tertiary"
                >
                  Clear
                </button>
                <button
                  onClick={() => setOpen(false)}
                  className="p-1 rounded hover:bg-bg-tertiary text-text-muted"
                >
                  <X size={14} />
                </button>
              </div>
            </div>

            {/* Log entries */}
            <div className="flex-1 overflow-y-auto px-3 py-2 font-mono text-xs space-y-0.5">
              {logs.length === 0 && (
                <div className="text-text-muted text-center py-8">
                  Waiting for scraper events...
                </div>
              )}
              {logs.map((entry) => (
                <div key={entry.id} className="flex gap-2">
                  <span className="text-text-muted shrink-0">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={typeColors[entry.type] ?? "text-text-secondary"}>
                    [{entry.type}]
                  </span>
                  <span className="text-text-secondary break-all">{entry.data}</span>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
