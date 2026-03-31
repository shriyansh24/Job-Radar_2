import { Bell, HardDrive, MagnifyingGlass, Palette, Plug, Shield, UserCircle } from "@phosphor-icons/react";
import type { AppSettings } from "../../api/settings";
import { parseThemePreference, serializeThemePreference } from "../../store/useUIStore";
import type { SearchEditorState } from "./SettingsSearchEditorModal";
import type { SettingsTab } from "./SettingsTabNav";

const SETTINGS_TABS: Array<{
  id: SettingsTab;
  label: string;
  icon: typeof UserCircle;
}> = [
  { id: "profile", label: "Profile", icon: UserCircle },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "workspace", label: "Workspace", icon: Bell },
  { id: "security", label: "Security", icon: Shield },
  { id: "integrations", label: "Integrations", icon: Plug },
  { id: "searches", label: "Searches", icon: MagnifyingGlass },
  { id: "data", label: "Data", icon: HardDrive },
];

const createInitialAppSettings = (): AppSettings => ({
  theme: "dark",
  notifications_enabled: true,
  auto_apply_enabled: false,
});

const createBlankSearchEditor = (): SearchEditorState => ({
  id: null,
  name: "",
  filtersText: JSON.stringify({}, null, 2),
  alertEnabled: true,
});

function normalizeAppSettings(settings: AppSettings): AppSettings {
  const { mode, themeFamily } = parseThemePreference(settings.theme);
  return {
    ...settings,
    theme: serializeThemePreference(themeFamily, mode),
  };
}

function parseSearchFilters(text: string): Record<string, unknown> {
  const trimmed = text.trim();
  if (!trimmed) return {};
  const parsed = JSON.parse(trimmed);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Saved search filters must be a JSON object");
  }
  return parsed as Record<string, unknown>;
}

export {
  SETTINGS_TABS,
  createBlankSearchEditor,
  createInitialAppSettings,
  normalizeAppSettings,
  parseSearchFilters,
};
