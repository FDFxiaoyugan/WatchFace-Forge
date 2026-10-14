"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Icon from "@/components/ui/Icon";
import { loadAIConfig, serverApiKeyHeaders, toAIRequestConfig, UserAIConfig, EMPTY_AI_CONFIG } from "@/lib/aiConfig";

interface GenerateResult {
  task_id: string;
  status: "success" | "failed";
  cdm?: any;
  fixes?: string[];
  backend?: string;
  attempts?: number;
  apk_filename?: string;
  apk_size?: number;
  download_url?: string;
  error?: string;
}

const EXAMPLE_PROMPTS = [
  "霓虹蓝赛博朋克风数字表盘",
  "极简白色细体表盘，大字号",
  "琥珀橙暖色表盘，显示电量和日期",
  "深紫色星空风格，霓虹紫时间",
];

export default function PromptInput({ onResult }: { onResult?: (r: GenerateResult) => void }) {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [aiConfig, setAIConfig] = useState<UserAIConfig>(EMPTY_AI_CONFIG);

  useEffect(() => setAIConfig(loadAIConfig()), []);

  async function handleGenerate() {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setElapsed(0);

    // 真实等待状态: 同步请求 + 已等待秒数（/api/generate 为同步长请求,
    // 服务端 task_id 在响应中返回, 期间无法预连 WS 取真实进度）
    const elapsedTimer = setInterval(() => setElapsed((s) => s + 1), 1000);

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...serverApiKeyHeaders() },
        body: JSON.stringify({ prompt, ai_config: toAIRequestConfig(aiConfig) }),
      });
      const data = await res.json();
      if (res.status === 401) {
        setResult({ task_id: "", status: "failed", error: "平台访问密钥无效或缺失，请在「设置」页配置 X-API-Key" });
        return;
      }
      if (res.status === 429) {
        setResult({ task_id: "", status: "failed", error: data?.error?.message || "生成配额已用尽，请稍后再试" });
        return;
      }
      if (res.status === 503) {
        setResult({ task_id: "", status: "failed", error: data?.error?.message || "服务暂不可用（密钥/配额后端未配置）" });
        return;
      }
      setResult(data);
      onResult?.(data);
    } catch (err) {
      setResult({ task_id: "", status: "failed", error: err instanceof Error ? err.message : String(err) });
    } finally {
      clearInterval(elapsedTimer);
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.15fr_.85fr]">
      <div className="rounded-[20px] bg-[#15191e] p-6 md:p-8">
        <div className="mb-6 flex items-start gap-4">
          <span className="md-feature-icon"><Icon name="spark" size={24}/></span>
          <div><h2 className="text-xl font-semibold">描述你的表盘</h2><p className="mt-1 text-sm text-forge-muted">AI 会生成结构化 CDM，并自动完成 WFF 编译与 APK 构建。</p></div>
        </div>

        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-forge-border bg-[#101318] px-4 py-3 text-sm">
          <span className="flex items-center gap-2 text-forge-muted"><Icon name="settings" size={17}/><span className={`h-2 w-2 rounded-full ${aiConfig.apiKey ? "bg-emerald-400" : "bg-amber-300"}`}/>{aiConfig.apiKey ? `自定义 API · ${aiConfig.model || "gpt-4o"}` : "使用服务端默认 AI"}</span>
          <button type="button" className="text-forge-accent hover:underline" onClick={() => router.push("/settings")}>配置 AI 服务</button>
        </div>

      {/* Input */}
      <div className="mb-3 flex flex-col gap-3 sm:flex-row">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleGenerate(); } }}
          placeholder="例如：黑色极简数字表盘，时间使用大号细体，显示日期和电量…"
          disabled={loading}
          rows={3}
          className="md-field min-h-[104px] flex-1 resize-none"
        />
        <button
          onClick={handleGenerate}
          disabled={loading || !prompt.trim()}
          className="md-button md-button--filled self-stretch sm:self-auto"
        >
          <Icon name="spark" size={18}/>{loading ? "生成中…" : "生成表盘"}
        </button>
      </div>

      {/* Example prompts */}
      {!loading && (
        <div className="flex flex-wrap gap-2 mb-4">
          {EXAMPLE_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => setPrompt(p)}
              className="md-chip cursor-pointer bg-transparent transition-colors hover:border-forge-accent hover:text-forge-accent"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* 等待状态（真实: 已等待时长, 非确定性假进度） */}
      {loading && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-forge-muted">AI 生成中…（完整链路通常 10–60 秒）</span>
            <span className="text-sm text-forge-accent">已等待 {elapsed}s</span>
          </div>
          <div className="md-progress overflow-hidden">
            <div className="h-full w-1/3 bg-forge-accent animate-pulse" />
          </div>
        </div>
      )}
      </div>

      <aside className="rounded-[20px] border border-forge-border bg-[#101318] p-6 md:p-8">
        <span className="md-label">生成流程</span>
        <ol className="mt-5 space-y-5">
          {["理解设计描述", "生成并校验 CDM", "编译 WFF XML", "签名并交付 APK"].map((item, index) => <li key={item} className="flex items-center gap-3 text-sm"><span className="grid h-7 w-7 place-items-center rounded-full bg-[#263e60] text-xs text-[#d3e3fd]">{index + 1}</span><span className="text-forge-muted">{item}</span></li>)}
        </ol>
        {!result && <div className="mt-8 rounded-2xl bg-[#1b1f24] p-4 text-sm leading-6 text-forge-muted">生成结果可直接下载，也能带入可视化编辑器继续调整。</div>}
        {result && <div className={`mt-8 rounded-2xl border p-4 ${result.status === "success" ? "border-emerald-800 bg-emerald-950/20" : "border-red-900 bg-red-950/20"}`}>
          <strong className={result.status === "success" ? "text-emerald-300" : "text-red-300"}>{result.status === "success" ? "生成完成" : "生成失败"}</strong>
          {result.status === "success" ? <div className="mt-4 flex flex-wrap gap-2">
            {result.download_url && <a className="md-button md-button--filled" href={result.download_url}><Icon name="download" size={17}/>下载 APK</a>}
            {result.task_id && <button className="md-button" onClick={() => router.push(`/editor?task_id=${result.task_id}`)}><Icon name="palette" size={17}/>继续编辑</button>}
          </div> : <p className="mt-2 text-sm text-red-200/80">{result.error || "AI 服务暂不可用，请检查模型配置。"}</p>}
        </div>}
      </aside>
    </div>
  );
}
