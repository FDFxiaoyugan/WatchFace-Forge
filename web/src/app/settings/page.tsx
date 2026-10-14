"use client";

import { FormEvent, useEffect, useState } from "react";
import AppShell from "@/components/ui/AppShell";
import Icon from "@/components/ui/Icon";
import { clearAIConfig, EMPTY_AI_CONFIG, loadAIConfig, loadServerApiKey, saveAIConfig, saveServerApiKey, serverApiKeyHeaders, toAIRequestConfig, UserAIConfig } from "@/lib/aiConfig";

export default function SettingsPage() {
  const [config, setConfig] = useState<UserAIConfig>(EMPTY_AI_CONFIG);
  const [platformKey, setPlatformKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"neutral" | "success" | "error">("neutral");
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    setConfig(loadAIConfig());
    setPlatformKey(loadServerApiKey());
  }, []);

  function savePlatformKey(value: string) {
    setPlatformKey(value);
    saveServerApiKey(value);
    if (value.trim()) {
      setMessage("平台访问密钥已保存到本浏览器（localStorage）");
      setMessageTone("success");
    } else {
      setMessage("平台访问密钥已清除");
      setMessageTone("neutral");
    }
  }

  function update(field: keyof UserAIConfig, value: string) {
    setConfig((current) => ({ ...current, [field]: value }));
    setMessage("");
    setMessageTone("neutral");
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!config.apiKey.trim()) {
      clearAIConfig();
      setConfig(EMPTY_AI_CONFIG);
      setMessage("已切换为服务端默认 AI");
      setMessageTone("neutral");
      return;
    }
    if (config.baseUrl && !config.baseUrl.startsWith("https://")) {
      setMessage("自定义 Base URL 必须使用 HTTPS");
      setMessageTone("error");
      return;
    }
    saveAIConfig(config);
    setConfig(loadAIConfig());
    setMessage("已保存到当前标签页，本次会话中的 AI 生成将使用此配置");
    setMessageTone("success");
  }

  async function testConnection() {
    const aiConfig = toAIRequestConfig(config);
    if (!aiConfig) {
      setMessage("请先填写自定义 AI API Key");
      setMessageTone("error");
      return;
    }
    if (config.baseUrl && !config.baseUrl.startsWith("https://")) {
      setMessage("自定义 Base URL 必须使用 HTTPS");
      setMessageTone("error");
      return;
    }

    setTesting(true);
    setMessage("正在验证密钥、接口地址和模型…");
    setMessageTone("neutral");
    try {
      const response = await fetch("/api/ai/test", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...serverApiKeyHeaders() },
        body: JSON.stringify({ ai_config: aiConfig }),
      });
      const payload = await response.json();
      if (response.status === 401) throw new Error("平台访问密钥无效或缺失（在下方「平台访问密钥」中配置）");
      if (response.status === 429) throw new Error(payload?.error?.message || "测试配额已用尽，请稍后再试");
      if (!response.ok) throw new Error(payload.message || payload?.error?.message || `HTTP ${response.status}`);
      setMessage(`连接成功 · ${payload.model} · ${payload.latency_ms} ms`);
      setMessageTone("success");
    } catch (error) {
      setMessage(`连接失败：${error instanceof Error ? error.message : String(error)}`);
      setMessageTone("error");
    } finally {
      setTesting(false);
    }
  }

  function reset() {
    clearAIConfig();
    setConfig(EMPTY_AI_CONFIG);
    setMessage("自定义配置已清除，已切换为服务端默认 AI");
    setMessageTone("neutral");
  }

  return <AppShell><main className="md-page">
    <header className="mb-8 max-w-3xl">
      <span className="md-eyebrow"><Icon name="settings" size={17}/>AI configuration</span>
      <h1 className="mt-3 text-4xl font-medium tracking-[-.04em]">AI 服务设置</h1>
      <p className="mt-3 text-forge-muted">为自然语言生成配置你自己的 OpenAI 兼容接口。这里的密钥与 Agent CI 使用的 X-API-Key 是两套独立凭据。</p>
    </header>

    <section className="grid max-w-5xl gap-5 lg:grid-cols-[1.2fr_.8fr]">
      <form onSubmit={submit} className="rounded-[22px] border border-forge-border bg-[#15191e] p-6 md:p-8">
        <div className="mb-6"><span className="md-label">PROVIDER</span><h2 className="mt-1 text-xl font-medium">OpenAI 兼容 API</h2></div>

        <label className="md-label" htmlFor="ai-api-key">API Key</label>
        <div className="mb-5 mt-2 flex gap-2">
          <input id="ai-api-key" type={showKey ? "text" : "password"} autoComplete="off" value={config.apiKey} onChange={(event) => update("apiKey", event.target.value)} placeholder="sk-…" className="md-field min-w-0 flex-1 font-mono text-sm" />
          <button type="button" className="md-button" onClick={() => setShowKey((value) => !value)}>{showKey ? "隐藏" : "显示"}</button>
        </div>

        <label className="md-label" htmlFor="ai-base-url">Base URL · 可选</label>
        <input id="ai-base-url" type="url" value={config.baseUrl} onChange={(event) => update("baseUrl", event.target.value)} placeholder="https://api.openai.com/v1" className="md-field mb-5 mt-2 font-mono text-sm" />
        <p className="-mt-3 mb-5 text-xs leading-5 text-forge-muted">留空时使用 OpenAI 官方地址；第三方兼容服务必须填写 HTTPS 地址。</p>

        <label className="md-label" htmlFor="ai-model">模型</label>
        <input id="ai-model" value={config.model} onChange={(event) => update("model", event.target.value)} placeholder="gpt-4o" className="md-field mt-2 font-mono text-sm" />

        {message && <div role="status" className={`mt-5 rounded-xl border px-4 py-3 text-sm ${messageTone === "success" ? "border-emerald-800 bg-emerald-950/20 text-emerald-300" : messageTone === "error" ? "border-red-900 bg-red-950/20 text-red-200" : "border-forge-border bg-[#101318] text-forge-muted"}`}>{message}</div>}

        <div className="mt-8 border-t border-forge-border pt-6">
          <label className="md-label" htmlFor="platform-key">平台访问密钥（X-API-Key）</label>
          <input
            id="platform-key"
            type={showKey ? "text" : "password"}
            autoComplete="off"
            value={platformKey}
            onChange={(event) => savePlatformKey(event.target.value)}
            placeholder="wff_…（由部署者通过 scripts/create-api-key.sh 签发）"
            className="md-field mt-2 w-full font-mono text-sm"
          />
          <p className="mt-2 text-xs leading-5 text-forge-muted">
            公网部署（WF_ENV=production）下生成与连接测试必须携带；本机开发可不填。
            保存在浏览器 localStorage，随每次生成请求发送，不进入日志。
          </p>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <button type="submit" className="md-button md-button--filled"><Icon name="check" size={17}/>保存会话配置</button>
          <button type="button" className="md-button md-button--tonal" onClick={testConnection} disabled={testing}>{testing ? "测试中…" : "测试连接"}</button>
          <button type="button" className="md-button" onClick={reset}>使用服务端默认</button>
        </div>
      </form>

      <aside className="rounded-[22px] border border-forge-border bg-[#101318] p-6 md:p-8">
        <span className="md-feature-icon"><Icon name="api" size={24}/></span>
        <h2 className="mt-5 text-lg font-medium">密钥如何使用</h2>
        <ul className="mt-4 space-y-4 text-sm leading-6 text-forge-muted">
          <li>仅保存在当前浏览器标签页的 sessionStorage 中。</li>
          <li>只在点击“生成表盘”时随该次请求发送给后端，不写入数据库、日志或项目文件。</li>
          <li>“测试连接”会发起一次最多 16 token 的真实模型请求，可能产生极少量 API 费用。</li>
          <li>关闭标签页后浏览器会清除配置；也可随时点击“使用服务端默认”。</li>
          <li>请只在可信的部署地址上输入密钥，并建议使用限额独立密钥。</li>
        </ul>
      </aside>
    </section>
  </main></AppShell>;
}
