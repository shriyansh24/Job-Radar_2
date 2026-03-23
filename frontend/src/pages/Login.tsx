import { ArrowRight, Sparkle, SpinnerGap } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { PageHeader } from "../components/system/PageHeader";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import { useAuthStore } from "../store/useAuthStore";

const HIGHLIGHTS = [
  "Light and dark modes are first-class, not afterthoughts.",
  "Career data, saved searches, and outcomes stay in one operating surface.",
  "Prepared for the new settings, prepare, and intelligence workspaces.",
];

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
    <div className="min-h-[100dvh] bg-background px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100dvh-3rem)] max-w-7xl items-center gap-6 lg:grid-cols-[1.1fr_minmax(360px,0.9fr)]">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          className="space-y-6"
        >
          <PageHeader
            eyebrow="JobRadar Career OS"
            title="Sign in"
            description="A calm, dense workspace for discovery, execution, preparation, and intelligence. The theme system is built to stay legible in both light and jet-black dark mode."
            meta={
              <>
                <span className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/80 px-3 py-1">
                  <Sparkle size={12} weight="fill" />
                  Productive by default
                </span>
              </>
            }
          />

          <div className="grid gap-3 sm:grid-cols-3">
            {HIGHLIGHTS.map((highlight) => (
              <StateBlock key={highlight} tone="muted" title={highlight} />
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.985 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1], delay: 0.03 }}
        >
          <Surface tone="default" padding="lg" radius="xl" className="shadow-[var(--shadow-lg)]">
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                  Account access
                </div>
                <h2 className="text-2xl font-semibold tracking-[-0.04em]">Welcome back</h2>
                <p className="text-sm leading-6 text-muted-foreground">
                  Enter the credentials for your workspace account. The rest of the app will keep your
                  design system, searches, and outcome history synchronized.
                </p>
              </div>

              <form className="space-y-4" onSubmit={handleSubmit}>
                {error ? (
                  <div className="rounded-[var(--radius-lg)] border border-[var(--color-accent-danger)]/25 bg-[var(--color-accent-danger)]/8 px-4 py-3 text-sm text-[var(--color-accent-danger)]">
                    {error}
                  </div>
                ) : null}

                <Input
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                />

                <Input
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                />

                <Button
                  type="submit"
                  className="w-full"
                  loading={loading}
                  icon={loading ? <SpinnerGap size={16} weight="bold" /> : <ArrowRight size={16} weight="bold" />}
                >
                  Sign in
                </Button>
              </form>
            </div>
          </Surface>
        </motion.div>
      </div>
    </div>
  );
}
