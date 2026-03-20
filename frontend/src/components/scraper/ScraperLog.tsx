import { CaretDown, Pause, Play, X } from "@phosphor-icons/react";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
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

  useEffect(() => {
    if (!open) return;

    const eventSource = new EventSource(scraperApi.stream());
    let mounted = true;

    eventSource.onmessage = (event) => {
      if (!mounted || paused) return;
      try {
        const parsed = JSON.parse(event.data) as ScraperEvent;
        setLogs((prev) => [
          ...prev.slice(-200), // Keep last 200 entries
          {
            id: ++idCounter.current,
            type: parsed.type,
            data: parsed.data,
            timestamp: parsed.timestamp || new Date().toISOString(),
          },
        ]);
      } catch {
        // Non-JSON event — add as raw text
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
    scraper_started: "text-blue-400",
    job_found: "text-green-400",
    scraper_completed: "text-green-300",
    scraper_error: "text-red-400",
    error: "text-red-400",
    info: "text-text-muted",
  };

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-4 right-4 z-40 flex items-center gap-2 px-3 py-2 rounded-[var(--radius-lg)] bg-bg-secondary border border-border shadow-lg text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
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
            className="fixed bottom-0 right-0 z-50 w-full max-w-lg h-64 border-t border-l border-border rounded-tl-[var(--radius-lg)] bg-bg-secondary shadow-2xl flex flex-col"
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
