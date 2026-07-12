export type UiLanguage = "de" | "en";
export type UiTheme = "system" | "light" | "dark";

export type GeneralSettings = {
  language: UiLanguage;
  theme: UiTheme;
  timezone: string;
};

export const GENERAL_SETTINGS_STORAGE_KEY = "local-chat-general-settings";

export const DEFAULT_GENERAL_SETTINGS: GeneralSettings = {
  language: "de",
  theme: "system",
  timezone: "Europe/Berlin",
};

function isLanguage(value: unknown): value is UiLanguage {
  return value === "de" || value === "en";
}

function isTheme(value: unknown): value is UiTheme {
  return value === "system" || value === "light" || value === "dark";
}

export function normalizeGeneralSettings(value: unknown): GeneralSettings {
  if (!value || typeof value !== "object") {
    return DEFAULT_GENERAL_SETTINGS;
  }

  const map = value as Record<string, unknown>;
  const language = isLanguage(map.language) ? map.language : DEFAULT_GENERAL_SETTINGS.language;
  const theme = isTheme(map.theme) ? map.theme : DEFAULT_GENERAL_SETTINGS.theme;
  const timezone =
    typeof map.timezone === "string" && map.timezone.trim().length > 0
      ? map.timezone.trim()
      : DEFAULT_GENERAL_SETTINGS.timezone;

  return { language, theme, timezone };
}

export function loadStoredGeneralSettings(): GeneralSettings {
  try {
    const raw = window.localStorage.getItem(GENERAL_SETTINGS_STORAGE_KEY);
    if (!raw) {
      return DEFAULT_GENERAL_SETTINGS;
    }
    return normalizeGeneralSettings(JSON.parse(raw));
  } catch {
    return DEFAULT_GENERAL_SETTINGS;
  }
}

export function storeGeneralSettings(settings: GeneralSettings): void {
  try {
    window.localStorage.setItem(GENERAL_SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Storage should not block runtime behavior.
  }
}

export function resolveTheme(theme: UiTheme): "light" | "dark" {
  if (theme === "light" || theme === "dark") {
    return theme;
  }
  if (typeof window.matchMedia !== "function") {
    return "light";
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyGeneralSettingsToDocument(settings: GeneralSettings): void {
  const root = typeof document !== "undefined" ? document.documentElement : null;
  if (!root) {
    return;
  }

  root.setAttribute("lang", settings.language);
  root.setAttribute("data-user-timezone", settings.timezone);
  root.setAttribute("data-ui-theme-preference", settings.theme);
  root.setAttribute("data-ui-theme", resolveTheme(settings.theme));
}
