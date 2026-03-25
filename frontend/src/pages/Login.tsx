import { ArrowRight, GithubLogo, GoogleLogo, ShieldCheck, Sparkle, SpinnerGap } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { useAuthStore } from "../store/useAuthStore";

const HIGHLIGHTS = [
  {
    title: "First-class themes",
    body: "Light and jet-black dark surfaces keep the same hierarchy and contrast.",
  },
  {
    title: "Operational context",
    body: "Career data, saved searches, and outcomes stay in one working surface.",
  },
  {
    title: "Mobile ready",
    body: "Phone and tablet layouts keep the login flow centered and legible.",
  },
];

const PANEL =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const TILE =
  "border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const FIELD =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] !shadow-none focus:!border-[var(--color-accent-primary)] focus:!ring-0";
const PRIMARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const SECONDARY_BUTTON =
  "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";

function BrutalStat({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className={`${TILE} p-4`}>
      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">
        {label}
      </div>
      <div className={`mt-3 font-mono text-3xl font-bold ${accent ?? ""}`}>{value}</div>
    </div>
  );
}

function FeatureCard({ title, body }: { title: string; body: string }) {
  return (
    <div className={`${TILE} p-4`}>
      <div className="text-sm font-bold uppercase tracking-[0.08em]">{title}</div>
      <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{body}</p>
    </div>
  );
}

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [keepSession, setKeepSession] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((state) => state.login);
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
    <div className="relative min-h-[100dvh] overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.10),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.10),transparent_30%)] dark:bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.18),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(255,255,255,0.05),transparent_26%)]" />
      <div className="pointer-events-none absolute left-6 top-6 hidden h-24 w-24 grid-cols-4 gap-1 opacity-20 sm:grid">
        {Array.from({ length: 16 }).map((_, index) => (
          <span key={index} className="border border-[var(--color-text-primary)]" />
        ))}
      </div>
      <div className="pointer-events-none absolute bottom-6 right-6 hidden text-[9rem] font-mono font-bold uppercase leading-none tracking-[-0.1em] text-[var(--color-text-primary)] opacity-[0.06] lg:block">
        LOGIN
      </div>

      <div className="relative mx-auto flex min-h-[100dvh] max-w-7xl items-center px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid w-full gap-6 lg:grid-cols-[1.08fr_minmax(380px,0.92fr)]">
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="space-y-6"
          >
            <div className={`${PANEL} p-6 sm:p-8`}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-bold uppercase tracking-[0.25em] text-[var(--color-accent-primary)]">
                    JobRadar Career OS
                  </div>
                  <h1 className="mt-2 text-4xl font-black uppercase tracking-tighter sm:text-5xl lg:text-6xl">
                    Command Center
                  </h1>
                </div>
                <div className="inline-flex items-center gap-2 border-2 border-[var(--color-text-primary)] px-3 py-2 text-[10px] font-bold uppercase tracking-[0.2em]">
                  <Sparkle size={14} weight="bold" />
                  Security gateway
                </div>
              </div>

              <p className="mt-5 max-w-2xl text-sm leading-7 text-[var(--color-text-secondary)] sm:text-base">
                Neo-brutalist access for a career operating system. The same workspace reads cleanly on
                desktop, tablet, and phone without losing hierarchy or contrast.
              </p>

              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                <BrutalStat label="Themes" value="02" accent="text-[var(--color-accent-primary)]" />
                <BrutalStat label="Routes" value="06" accent="text-[var(--color-accent-success)]" />
                <BrutalStat label="Modes" value="01" accent="text-[var(--color-accent-warning)]" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {HIGHLIGHTS.map((item) => (
                <FeatureCard key={item.title} title={item.title} body={item.body} />
              ))}
            </div>

            <div className={`${PANEL} grid gap-4 p-5 sm:grid-cols-2`}>
              <div className="space-y-2">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">
                  Access notes
                </div>
                <p className="text-sm leading-6 text-[var(--color-text-secondary)]">
                  Login is the only standalone page. Everything after this point uses the shared workspace
                  shell and should feel like one operating surface.
                </p>
              </div>
              <div className="space-y-2">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">
                  Theme contract
                </div>
                <p className="text-sm leading-6 text-[var(--color-text-secondary)]">
                  Light mode stays warm and paper-like. Dark mode stays near-black with crisp borders and
                  hard shadows.
                </p>
              </div>
            </div>
          </motion.section>

          <motion.section
            initial={{ opacity: 0, y: 20, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1], delay: 0.03 }}
            className="self-center"
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

                <label className="flex items-center gap-3 border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-primary)] px-4 py-3 text-sm">
                  <input
                    type="checkbox"
                    checked={keepSession}
                    onChange={(event) => setKeepSession(event.target.checked)}
                    className="size-4 rounded-none border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)] accent-[var(--color-accent-primary)]"
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
