import { createBrowserRouter } from "react-router";
import { AppShell } from "./AppShell";
import { Dashboard } from "./pages/Dashboard";
import { JobBoard } from "./pages/Jobs";
import { Pipeline } from "./pages/Pipeline";
import { Settings } from "./pages/Settings";
import { Login } from "./pages/Login";
import { Analytics } from "./pages/Analytics";
import { Copilot } from "./pages/Copilot";
import { GenericPage } from "./pages/GenericPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/",
    Component: AppShell,
    children: [
      { index: true, Component: Dashboard },
      { path: "jobs", Component: JobBoard },
      { path: "pipeline", Component: Pipeline },
      { path: "settings", Component: Settings },
      { path: "analytics", Component: Analytics },
      { path: "copilot", Component: Copilot },
      { path: "companies", Component: GenericPage },
      { path: "auto-apply", Component: GenericPage },
      { path: "networking", Component: GenericPage },
      { path: "email", Component: GenericPage },
      { path: "resume", Component: GenericPage },
      { path: "interview", Component: GenericPage },
      { path: "salary", Component: GenericPage },
      { path: "vault", Component: GenericPage },
      { path: "outcomes", Component: GenericPage },
      { path: "profile", Component: GenericPage },
      { path: "sources", Component: GenericPage },
      { path: "targets", Component: GenericPage },
      { path: "canonical-jobs", Component: GenericPage },
      { path: "search-expansion", Component: GenericPage },
      { path: "admin", Component: GenericPage },
      { path: "*", Component: GenericPage },
    ],
  },
]);