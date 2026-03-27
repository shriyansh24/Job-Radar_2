import {
  ArrowRight,
  GithubLogo,
  GoogleLogo,
  ShieldCheck,
  SpinnerGap,
  Sun,
  Moon,
  Sparkle,
} from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { type FormEvent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import { useAuthStore } from "../store/useAuthStore";
import { useUIStore } from "../store/useUIStore";

const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white dark:!bg-blue-700 dark:hover:!bg-blue-800 transition-colors";
const SECONDARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5";

function formatThemeFamily(themeFamily: string) {
  return themeFamily.charAt(0).toUpperCase() + themeFamily.slice(1);
}

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [keepSession, setKeepSession] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((state) => state.login);
  const { theme, themeFamily, toggleTheme } = useUIStore();
  const navigate = useNavigate();

  const themeBadges = useMemo(
    () => [
      { label: formatThemeFamily(themeFamily), variant: "info" as const },
      { label: theme === "dark" ? "Jet-black dark" : "Light canvas", variant: "secondary" as const },
      { label: "Theme toggle", variant: "default" as const },
    ],
    [theme, themeFamily]
  );

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (reason: unknown) {
      const message =
        reason instanceof Error &&
        (reason.message.includes("Network") || reason.message.includes("ECONNREFUSED"))
          ? "Unable to reach the backend."
          : "Invalid email or password.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-[100dvh] overflow-hidden bg-background text-foreground dark:bg-black">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(16,185,129,0.10),transparent_28%)] dark:bg-none" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-border/70" />
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-24 bg-[linear-gradient(to_top,rgba(0,0,0,0.04),transparent)] dark:bg-[linear-gradient(to_top,rgba(255,255,255,0.04),transparent)]" />

      <div className="absolute right-6 top-6 z-10">
        <button
          onClick={toggleTheme}
          className="flex size-10 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] text-[var(--color-text-primary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5 active:scale-95"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={20} weight="bold" /> : <Moon size={20} weight="bold" />}
        </button>
      </div>

      <div className="relative mx-auto flex min-h-[100dvh] w-full max-w-6xl items-center px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid w-full gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(380px,0.9fr)]">
          <motion.section
            initial={{ opacity: 0, y: 20, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1], delay: 0.03 }}
            className="flex"
          >
            <Surface
              tone="default"
              padding="lg"
              radius="xl"
              className="flex h-full w-full flex-col justify-between overflow-hidden bg-[var(--color-bg-secondary)]"
            >
              <div className="space-y-6">
                <div className="flex flex-wrap items-center gap-2">
                  {themeBadges.map((badge) => (
                    <Badge key={badge.label} variant={badge.variant} size="sm" className="rounded-none">
                      {badge.label}
                    </Badge>
                  ))}
                </div>

                <div className="space-y-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-[var(--color-text-muted)]">
                    Authentication gateway
                  </div>
                  <h1 className="font-display text-[clamp(2.6rem,6vw,4.7rem)] font-black uppercase leading-[0.88] tracking-[-0.08em] text-[var(--color-text-primary)]">
                    Sign in to the workspace
                  </h1>
                  <p className="max-w-xl text-sm leading-7 text-[var(--color-text-secondary)] sm:text-base">
                    Access the command center with a real backend session. This page keeps the login
                    flow lean, high-contrast, and ready for keyboard or touch input.
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <StateBlock
                    tone="neutral"
                    icon={<ShieldCheck size={18} weight="bold" />}
                    title="Secure session"
                    description="Backend-issued auth cookies and token rotation."
                  />
                  <StateBlock
                    tone="warning"
                    icon={<Sparkle size={18} weight="bold" />}
                    title="Theme-aware"
                    description="Light, dark, and theme families stay available after login."
                  />
                  <StateBlock
                    tone="success"
                    icon={<ArrowRight size={18} weight="bold" />}
                    title="Fast path"
                    description="One form, no onboarding detours, straight into the shell."
                  />
                </div>
              </div>

              <div className="mt-6 border-t-2 border-[var(--color-text-primary)] pt-5 text-xs leading-6 text-[var(--color-text-secondary)]">
                JWT or session handling is always delegated to the backend. The page only gathers
                credentials and hands off to the auth flow.
              </div>
            </Surface>
          </motion.section>

          <motion.section
            initial={{ opacity: 0, y: 20, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1], delay: 0.08 }}
            className="flex"
          >
            <Surface
              tone="default"
              padding="none"
              radius="xl"
              className="flex h-full w-full flex-col overflow-hidden bg-[var(--color-bg-secondary)]"
            >
                <div className="border-b-2 border-[var(--color-text-primary)] px-5 py-4 sm:px-6">
                  <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-[var(--color-text-muted)]">
                    Sign-in panel
                  </div>
                  <h2 className="mt-2 font-display text-3xl font-black uppercase tracking-[-0.06em] text-[var(--color-text-primary)]">
                    Sign in
                  </h2>
                  <div className="mt-2 text-sm font-bold uppercase tracking-[0.18em] text-[var(--color-text-primary)]">
                    Welcome back
                  </div>
                  <p className="mt-2 max-w-md text-sm leading-6 text-[var(--color-text-secondary)]">
                    Enter your credentials to unlock the route families, the current theme, and the
                    backend-backed workspace state.
                  </p>
                </div>

              <form className="space-y-4 px-5 py-5 sm:px-6" onSubmit={handleSubmit}>
                {error ? (
                  <div className="border-2 border-[var(--color-accent-danger)] bg-[var(--color-accent-danger-subtle)] px-4 py-3 text-sm font-medium text-[var(--color-accent-danger)]">
                    {error}
                  </div>
                ) : null}

                <Input
                  label="Email address"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className={FIELD}
                />

                <Input
                  label="Password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter password"
                  className={FIELD}
                />

                <label className="flex cursor-pointer items-center gap-3 border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] px-4 py-3 text-sm">
                  <input
                    type="checkbox"
                    checked={keepSession}
                    onChange={(event) => setKeepSession(event.target.checked)}
                    className="size-4 cursor-pointer rounded-none border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] accent-[var(--color-accent-primary)]"
                  />
                  <span className="font-medium uppercase tracking-[0.08em]">Keep session active</span>
                </label>

                <Button
                  type="submit"
                  className={`w-full justify-center ${PRIMARY_BUTTON}`}
                  loading={loading}
                  icon={loading ? <SpinnerGap size={16} weight="bold" /> : <ArrowRight size={16} weight="bold" />}
                >
                  Sign in
                </Button>
              </form>

              <div className="border-t-2 border-[var(--color-text-primary)] px-5 py-5 sm:px-6">
                <div className="flex items-center gap-3">
                  <div className="h-px flex-1 bg-[var(--color-text-primary)]" />
                  <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-[var(--color-text-muted)]">
                    Security protocol
                  </div>
                  <div className="h-px flex-1 bg-[var(--color-text-primary)]" />
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Button
                    type="button"
                    variant="secondary"
                    className={`justify-start ${SECONDARY_BUTTON}`}
                    icon={<GithubLogo size={16} weight="bold" />}
                  >
                    GitHub
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    className={`justify-start ${SECONDARY_BUTTON}`}
                    icon={<GoogleLogo size={16} weight="bold" />}
                  >
                    Google
                  </Button>
                </div>

                <div className="mt-4 flex items-center gap-2 border-2 border-dashed border-[var(--color-text-primary)] px-4 py-3 text-xs text-[var(--color-text-secondary)]">
                  <ShieldCheck size={16} weight="bold" className="shrink-0 text-[var(--color-accent-primary)]" />
                  Session handling, redirects, and token exchange are still handled by the backend.
                </div>
              </div>
            </Surface>
          </motion.section>
        </div>
      </div>
    </div>
  );
}
