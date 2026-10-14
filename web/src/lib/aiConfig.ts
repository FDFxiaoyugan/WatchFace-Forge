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

// ─── 平台访问密钥（X-API-Key，服务端签发，区别于 BYOK）──────────────
// 部署者通过 scripts/create-api-key.sh 生成并分发给用户；generate/ai-test
// 在公网（WF_ENV=production + WFF_API_KEYS）模式下必须携带。
const SERVER_API_KEY_STORAGE = "wff_server_api_key";

export function loadServerApiKey(): string {
  if (typeof window === "undefined") return "";
  try {
    return window.localStorage.getItem(SERVER_API_KEY_STORAGE) || "";
  } catch {
    return "";
  }
}

export function saveServerApiKey(key: string): void {
  if (typeof window === "undefined") return;
  const trimmed = key.trim();
  if (!trimmed) {
    window.localStorage.removeItem(SERVER_API_KEY_STORAGE);
    return;
  }
  window.localStorage.setItem(SERVER_API_KEY_STORAGE, trimmed);
}

export function serverApiKeyHeaders(): Record<string, string> {
  const key = loadServerApiKey();
  return key ? { "X-API-Key": key } : {};
}
