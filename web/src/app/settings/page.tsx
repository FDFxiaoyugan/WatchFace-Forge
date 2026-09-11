"use client";

import { FormEvent, useEffect, useState } from "react";
import AppShell from "@/components/ui/AppShell";
import Icon from "@/components/ui/Icon";
import { clearAIConfig, EMPTY_AI_CONFIG, loadAIConfig, saveAIConfig, UserAIConfig } from "@/lib/aiConfig";

export default function SettingsPage() {
  const [config, setConfig] = useState<UserAIConfig>(EMPTY_AI_CONFIG);
  const [showKey, setShowKey] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => setConfig(loadAIConfig()), []);

  function update(field: keyof UserAIConfig, value: string) {
    setConfig((current) => ({ ...current, [field]: value }));
    setMessage("");
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!config.apiKey.trim()) {
      clearAIConfig();
      setConfig(EMPTY_AI_CONFIG);
      setMessage("已切换为服务端默认 AI");
      return;
    }
    if (config.baseUrl && !config.baseUrl.startsWith("https://")) {
      setMessage("自定义 Base URL 必须使用 HTTPS");
      return;
    }
    saveAIConfig(config);
    setConfig(loadAIConfig());
    setMessage("已保存到当前标签页，本次会话中的 AI 生成将使用此配置");
  }

  function reset() {
    clearAIConfig();
    setConfig(EMPTY_AI_CONFIG);
    setMessage("自定义配置已清除，已切换为服务端默认 AI");
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

        {message && <div role="status" className="mt-5 rounded-xl bg-[#101318] px-4 py-3 text-sm text-forge-muted">{message}</div>}
        <div className="mt-6 flex flex-wrap gap-3">
          <button type="submit" className="md-button md-button--filled"><Icon name="check" size={17}/>保存会话配置</button>
          <button type="button" className="md-button" onClick={reset}>使用服务端默认</button>
        </div>
      </form>

      <aside className="rounded-[22px] border border-forge-border bg-[#101318] p-6 md:p-8">
        <span className="md-feature-icon"><Icon name="api" size={24}/></span>
        <h2 className="mt-5 text-lg font-medium">密钥如何使用</h2>
        <ul className="mt-4 space-y-4 text-sm leading-6 text-forge-muted">
          <li>仅保存在当前浏览器标签页的 sessionStorage 中。</li>
          <li>只在点击“生成表盘”时随该次请求发送给后端，不写入数据库、日志或项目文件。</li>
          <li>关闭标签页后浏览器会清除配置；也可随时点击“使用服务端默认”。</li>
          <li>请只在可信的部署地址上输入密钥，并建议使用限额独立密钥。</li>
        </ul>
      </aside>
    </section>
  </main></AppShell>;
}
