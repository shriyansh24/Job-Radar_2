import { type ReactNode, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";

export default function AuthGuard({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const initialized = useAuthStore((s) => s.initialized);
  const loadFromSession = useAuthStore((s) => s.loadFromSession);
  const navigate = useNavigate();

  useEffect(() => {
    if (!initialized) {
      void loadFromSession();
    }
  }, [initialized, loadFromSession]);

  useEffect(() => {
    if (initialized && !isAuthenticated) {
      navigate("/login", { replace: true });
    }
  }, [initialized, isAuthenticated, navigate]);

  if (!initialized || !isAuthenticated) return null;
  return <>{children}</>;
}
