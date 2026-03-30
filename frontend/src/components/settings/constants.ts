import type { IntegrationStatus } from "../../api/settings";
import type { ThemeFamily, ThemeMode } from "../../store/useUIStore";

type SearchEditorState = {
  id: string | null;
  name: string;
  filtersText: string;
  alertEnabled: boolean;
};

const THEME_MODE_OPTIONS: Array<{ value: ThemeMode; label: string }> = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

const THEME_FAMILY_OPTIONS: Array<{ value: ThemeFamily; label: string }> = [
  { value: "default", label: "Default" },
  { value: "terminal", label: "Terminal" },
  { value: "blueprint", label: "Blueprint" },
  { value: "phosphor", label: "Phosphor" },
];

const INTEGRATION_LABELS: Record<IntegrationStatus["provider"], string> = {
  openrouter: "OpenRouter",
  serpapi: "SerpAPI",
  theirstack: "TheirStack",
  apify: "Apify",
};

const INTEGRATION_NOTES: Record<IntegrationStatus["provider"], string> = {
  openrouter: "Copilot and other model-backed tools.",
  serpapi: "Search coverage for discovery flows.",
  theirstack: "Company and market enrichment.",
  apify: "Scraper expansion and long-running jobs.",
};

export type { SearchEditorState };
export { THEME_MODE_OPTIONS, THEME_FAMILY_OPTIONS, INTEGRATION_LABELS, INTEGRATION_NOTES };
