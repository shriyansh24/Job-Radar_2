import { SpinnerGap } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/useAuthStore";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err: unknown) {
      const isNetworkError =
        err instanceof Error && (err.message.includes("Network") || err.message.includes("ECONNREFUSED"));
      setError(
        isNetworkError
          ? "Unable to connect to server. Please check your connection."
          : "Invalid email or password"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-primary relative overflow-hidden">
      {/* Subtle gradient orb */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-[0.03] pointer-events-none"
        style={{
          background: "radial-gradient(circle, var(--color-accent-primary) 0%, transparent 70%)",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="relative w-full max-w-sm mx-4"
      >
        <div className="p-8 bg-bg-secondary rounded-[var(--radius-2xl)] border border-border shadow-[var(--shadow-xl)]">
          {/* Logo */}
          <div className="text-center mb-8">
            <h1 className="text-xl font-bold tracking-[-0.03em] text-text-primary">
              JobRadar
              <span className="ml-1.5 text-[10px] font-mono px-1.5 py-0.5 rounded-[var(--radius-sm)] bg-accent-primary/10 text-accent-primary font-medium align-middle">
                v2
              </span>
            </h1>
            <p className="mt-2 text-sm text-text-muted">
              Sign in to your account
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="p-3 rounded-[var(--radius-md)] bg-accent-danger/8 border border-accent-danger/20 text-accent-danger text-sm"
              >
                {error}
              </motion.div>
            )}

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5 tracking-wide">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2.5 bg-bg-primary border border-border rounded-[var(--radius-lg)] text-sm text-text-primary placeholder:text-text-muted/60 focus:outline-none focus:border-border-focus focus:shadow-[var(--shadow-glow)] transition-[border-color,box-shadow] duration-[var(--transition-fast)]"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5 tracking-wide">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2.5 bg-bg-primary border border-border rounded-[var(--radius-lg)] text-sm text-text-primary placeholder:text-text-muted/60 focus:outline-none focus:border-border-focus focus:shadow-[var(--shadow-glow)] transition-[border-color,box-shadow] duration-[var(--transition-fast)]"
                placeholder="••••••••"
              />
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              whileTap={{ scale: 0.98 }}
              className="w-full py-2.5 mt-2 bg-accent-primary text-white text-sm font-medium rounded-[var(--radius-lg)] hover:brightness-110 disabled:opacity-50 transition-[filter,transform] duration-[var(--transition-fast)] shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)] flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <SpinnerGap size={16} weight="bold" className="animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
