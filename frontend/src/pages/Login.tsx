import { ArrowRight, GithubLogo, GoogleLogo, ShieldCheck, SpinnerGap, Sun, Moon } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { useAuthStore } from "../store/useAuthStore";
import { useUIStore } from "../store/useUIStore";

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]";
const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white dark:!bg-blue-700 dark:hover:!bg-blue-800 transition-colors";
const SECONDARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [keepSession, setKeepSession] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((state) => state.login);
  const { theme, toggleTheme } = useUIStore();
  const navigate = useNavigate();

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
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.10),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.10),transparent_30%)] dark:bg-none" />

      <div className="absolute right-6 top-6 z-10">
        <button
          onClick={toggleTheme}
          className="flex size-10 items-center justify-center border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] text-[var(--color-text-primary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5 active:scale-95"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={20} weight="bold" /> : <Moon size={20} weight="bold" />}
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
              <div className="border-b-2 border-[var(--color-text-primary)] px-5 py-4 sm:px-6">
                <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-[var(--color-text-muted)]">
                  Authentication Gateway V2.0.4
                </div>
                <h2 className="mt-2 text-2xl font-black uppercase tracking-tighter">
                  Sign in
                </h2>
                <div className="mt-2 text-sm font-bold uppercase tracking-[0.18em] text-[var(--color-text-primary)]">
                  Welcome back
                </div>
                <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">
                  Enter your credentials to access the command center.
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
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className={FIELD}
                />

                <Input
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  className={FIELD}
                />

                <label className="flex items-center gap-3 border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] px-4 py-3 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={keepSession}
                    onChange={(event) => setKeepSession(event.target.checked)}
                    className="size-4 rounded-none border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] accent-[var(--color-accent-primary)] cursor-pointer"
                  />
                  <span className="font-medium uppercase tracking-[0.08em]">
                    Keep session active
                  </span>
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
