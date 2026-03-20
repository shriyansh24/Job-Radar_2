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
    <div className="min-h-screen flex items-center justify-center bg-bg-primary">
      <div className="w-full max-w-md p-8 bg-bg-secondary rounded-[var(--radius-xl)] border border-border shadow-[var(--shadow-lg)]">
        <h1 className="text-2xl font-bold text-center mb-2 text-text-primary">
          JobRadar V2
        </h1>
        <p className="text-center text-text-muted mb-6">
          Sign in to your account
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-[var(--radius-md)] bg-accent-danger/10 text-accent-danger text-sm">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm text-text-secondary mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-[var(--radius-md)] text-text-primary focus:outline-none focus:border-border-focus"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm text-text-secondary mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-[var(--radius-md)] text-text-primary focus:outline-none focus:border-border-focus"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-accent-primary text-white font-medium rounded-[var(--radius-md)] hover:bg-accent-primary/90 disabled:opacity-50 transition-colors"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
