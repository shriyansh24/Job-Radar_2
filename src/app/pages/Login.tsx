import React, { useState } from "react";
import { useNavigate } from "react-router";
import { ArrowRight, Github, Chrome, ShieldCheck, Loader2, Sun, Moon } from "lucide-react";
import { motion } from "framer-motion";
import { useTheme } from "../theme-provider";

const PANEL = "border-2 border-border bg-secondary shadow-hard-xl";
const FIELD = "!rounded-none !border-2 !border-border !bg-secondary !text-foreground placeholder:!text-muted-foreground focus:!border-primary focus:!ring-0";
const PRIMARY_BUTTON = "!rounded-none !border-2 !border-border !bg-primary !text-primary-foreground dark:!bg-blue-700 dark:hover:!bg-blue-800 transition-colors shadow-hard-xl";
const SECONDARY_BUTTON = "!rounded-none !border-2 !border-border !bg-secondary !text-foreground transition-colors hover:bg-black/5 dark:hover:bg-white/5 shadow-hard-sm";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [keepSession, setKeepSession] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { mode, toggleMode } = useTheme();
  const navigate = useNavigate();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);

    setTimeout(() => {
      navigate("/", { replace: true });
    }, 800);
  }

  return (
    <div className="relative min-h-[100dvh] overflow-hidden bg-background text-foreground dark:bg-black">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.10),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.10),transparent_30%)] dark:bg-none" />

      <div className="absolute right-6 top-6 z-10">
        <button
          onClick={toggleMode}
          className="flex size-10 items-center justify-center border-2 border-border bg-secondary text-foreground transition-colors hover:bg-black/5 dark:hover:bg-white/5 active:scale-95"
          aria-label="Toggle theme"
        >
          {mode === "dark" ? <Sun size={20} strokeWidth={2.5} /> : <Moon size={20} strokeWidth={2.5} />}
        </button>
      </div>

      <div className="relative mx-auto flex min-h-[100dvh] max-w-md items-center justify-center px-4 py-6 sm:px-6 lg:px-8">
        <div className="w-full">
          <motion.section
            initial={{ opacity: 0, y: 20, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1], delay: 0.03 }}
          >
            <div className={`${PANEL} overflow-hidden`}>
              <div className="border-b-2 border-border px-5 py-4 sm:px-6">
                <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                  Authentication Gateway V2.0.4
                </div>
                <h2 className="mt-2 font-headline text-2xl font-black uppercase tracking-tighter">
                  Sign in
                </h2>
                <div className="mt-2 font-headline text-sm font-bold uppercase tracking-widest text-foreground">
                  Welcome back
                </div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Enter your credentials to access the command center.
                </p>
              </div>

              <form className="space-y-4 px-5 py-5 sm:px-6" onSubmit={handleSubmit}>
                {error ? (
                  <div className="border-2 border-red-600 bg-red-600/10 px-4 py-3 text-sm font-medium text-red-600">
                    {error}
                  </div>
                ) : null}

                <div className="space-y-1">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Email address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    className={`w-full px-4 py-2.5 font-mono text-sm ${FIELD}`}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="••••••••"
                    className={`w-full px-4 py-2.5 font-mono text-sm ${FIELD}`}
                  />
                </div>

                <label className="flex items-center gap-3 border-2 border-border bg-background px-4 py-3 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={keepSession}
                    onChange={(event) => setKeepSession(event.target.checked)}
                    className="size-4 rounded-none border-2 border-border bg-secondary accent-primary cursor-pointer"
                  />
                  <span className="font-medium uppercase tracking-widest">
                    Keep session active
                  </span>
                </label>

                <button
                  type="submit"
                  disabled={loading}
                  className={`hard-press flex w-full items-center justify-center gap-2 px-4 py-4 font-headline text-lg font-black uppercase tracking-widest ${PRIMARY_BUTTON}`}
                >
                  {loading ? <Loader2 size={16} strokeWidth={2.5} className="animate-spin" /> : <ArrowRight size={16} strokeWidth={2.5} />}
                  Enter Radar
                </button>
              </form>

              <div className="border-t-2 border-border px-5 py-5 sm:px-6">
                <div className="flex items-center gap-3">
                  <div className="h-px flex-1 bg-border" />
                  <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                    Security protocol
                  </div>
                  <div className="h-px flex-1 bg-border" />
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <button
                    type="button"
                    className={`hard-press flex items-center justify-start gap-2 px-4 py-2.5 font-sans text-[11px] font-black uppercase tracking-widest ${SECONDARY_BUTTON}`}
                  >
                    <Github size={16} strokeWidth={2.5} />
                    GitHub
                  </button>
                  <button
                    type="button"
                    className={`hard-press flex items-center justify-start gap-2 px-4 py-2.5 font-sans text-[11px] font-black uppercase tracking-widest ${SECONDARY_BUTTON}`}
                  >
                    <Chrome size={16} strokeWidth={2.5} />
                    Google
                  </button>
                </div>

                <div className="mt-4 flex items-center gap-2 border-2 border-dashed border-border px-4 py-3 text-xs text-muted-foreground">
                  <ShieldCheck size={16} strokeWidth={2.5} className="shrink-0 text-primary" />
                  AES-256 encrypted session handling and token rotation are handled by the backend.
                </div>
              </div>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
}