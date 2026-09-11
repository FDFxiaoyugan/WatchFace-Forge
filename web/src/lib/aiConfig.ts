export type UserAIConfig = {
  apiKey: string;
  baseUrl: string;
  model: string;
};

export type UserAIRequestConfig = {
  api_key: string;
  base_url: string;
  model: string;
};

export const AI_CONFIG_SESSION_KEY = "wff_user_ai_config";
export const DEFAULT_AI_MODEL = "gpt-4o";

export const EMPTY_AI_CONFIG: UserAIConfig = {
  apiKey: "",
  baseUrl: "",
  model: DEFAULT_AI_MODEL,
};

export function loadAIConfig(): UserAIConfig {
  if (typeof window === "undefined") return EMPTY_AI_CONFIG;
  try {
    const raw = window.sessionStorage.getItem(AI_CONFIG_SESSION_KEY);
    if (!raw) return EMPTY_AI_CONFIG;
    const value = JSON.parse(raw) as Partial<UserAIConfig>;
    return {
      apiKey: typeof value.apiKey === "string" ? value.apiKey : "",
      baseUrl: typeof value.baseUrl === "string" ? value.baseUrl : "",
      model: typeof value.model === "string" && value.model.trim() ? value.model : DEFAULT_AI_MODEL,
    };
  } catch {
    window.sessionStorage.removeItem(AI_CONFIG_SESSION_KEY);
    return EMPTY_AI_CONFIG;
  }
}

export function saveAIConfig(config: UserAIConfig): void {
  if (typeof window === "undefined") return;
  const normalized = {
    apiKey: config.apiKey.trim(),
    baseUrl: config.baseUrl.trim(),
    model: config.model.trim() || DEFAULT_AI_MODEL,
  };
  if (!normalized.apiKey) {
    window.sessionStorage.removeItem(AI_CONFIG_SESSION_KEY);
    return;
  }
  window.sessionStorage.setItem(AI_CONFIG_SESSION_KEY, JSON.stringify(normalized));
}

export function clearAIConfig(): void {
  if (typeof window !== "undefined") window.sessionStorage.removeItem(AI_CONFIG_SESSION_KEY);
}

export function toAIRequestConfig(config: UserAIConfig): UserAIRequestConfig | undefined {
  const apiKey = config.apiKey.trim();
  if (!apiKey) return undefined;
  return {
    api_key: apiKey,
    base_url: config.baseUrl.trim(),
    model: config.model.trim() || DEFAULT_AI_MODEL,
  };
}
