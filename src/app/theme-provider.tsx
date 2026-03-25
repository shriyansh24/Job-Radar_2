import React, { createContext, useContext, useEffect, useState } from "react";

export type Theme = "default" | "terminal" | "blueprint" | "phosphor";
export type Mode = "light" | "dark";

interface ThemeProviderState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  mode: Mode;
  setMode: (mode: Mode) => void;
  toggleMode: () => void;
}

const initialState: ThemeProviderState = {
  theme: "default",
  setTheme: () => null,
  mode: "light",
  setMode: () => null,
  toggleMode: () => null,
};

const ThemeProviderContext = createContext<ThemeProviderState>(initialState);

export function ThemeProvider({
  children,
  defaultTheme = "default",
  defaultMode = "light",
}: {
  children: React.ReactNode;
  defaultTheme?: Theme;
  defaultMode?: Mode;
}) {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem("jobradar-theme") as Theme) || defaultTheme
  );
  const [mode, setMode] = useState<Mode>(
    () => (localStorage.getItem("jobradar-mode") as Mode) || defaultMode
  );

  useEffect(() => {
    const root = window.document.documentElement;

    root.classList.remove("light", "dark");
    root.classList.add(mode);

    if (theme === "default") {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", theme);
    }
  }, [theme, mode]);

  const value = {
    theme,
    setTheme: (newTheme: Theme) => {
      localStorage.setItem("jobradar-theme", newTheme);
      setTheme(newTheme);
    },
    mode,
    setMode: (newMode: Mode) => {
      localStorage.setItem("jobradar-mode", newMode);
      setMode(newMode);
    },
    toggleMode: () => {
      const newMode = mode === "light" ? "dark" : "light";
      localStorage.setItem("jobradar-mode", newMode);
      setMode(newMode);
    }
  };

  return (
    <ThemeProviderContext.Provider value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext);
  if (context === undefined)
    throw new Error("useTheme must be used within a ThemeProvider");
  return context;
};